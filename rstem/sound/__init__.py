#
# Copyright (c) 2014, Scott Silver Labs, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
'''
This module provides interfaces to the Speaker RaspberrySTEM Cell.

Additionally, it can be used for any audio out over the analog audio jack.
'''

import os
import sys
import time
import re
import io
from functools import partial
from . import mixer     # c extension
import tempfile
from threading import RLock, Thread, Condition, Event
from queue import Queue, Full
from subprocess import call, check_output
from struct import pack, unpack
import math

'''
    Future Sound class member function:
        def seek(self, position, absolute=False, percentage=False)
            - relative +/- seconds
            - absolute +/- seconds (-negative seconds from end)
            - absolute percentage
            - returns previous position, in seconds
'''

STOP, PLAY, FLUSH = range(3)
CHUNK_BYTES = 1024
SOUND_CACHE = '/home/pi/.rstem_sounds'

def shell_cmd(cmd):
    with open(os.devnull, "w") as devnull:
        call(cmd, stdout=devnull, stderr=devnull)

def master_volume(level):
    if level < 0 or level > 100:
        raise ValueError("level must be between 0 and 100.")

    shell_cmd('amixer sset PCM {}%'.format(int(level)).split())

class Players(object):
    def __init__(self):
        mixer.init()
        self.mutex = RLock()
        self.players = set()
        self.thread = Thread(target=self.daemon)
        self.thread.daemon = True
        self.thread.start()

    def add(self, sound):
        with self.mutex:
            self.players.add(sound)

    def remove(self, sound):
        with self.mutex:
            try:
                self.players.remove(sound)
            except KeyError:
                # Ignore deleting the same sound multiple times (of course,
                # also means we're ignoring deleting an invalid sound).
                pass

    def daemon(self):
        chunk = None
        while True:
            starting_sounds = []
            chunks = []
            gains = []
            with self.mutex:
                # For each player, get an audio buffer.
                for sound in frozenset(self.players):
                    count, chunk, gain = sound.play_q.get()
                    if count >= 0:
                        if count == 0:
                            starting_sounds.append(sound)
                        chunks.append(chunk)
                        gains.append(gain)
                    else:
                        sound.flush_done.set()
                        self.remove(sound)
            if chunks:
                for sound in starting_sounds:
                    sound.start_time = time.time()
                mixer.play(chunks, gains)
            else:
                mixer.play([bytes(CHUNK_BYTES)], [1])

class BaseSound(object):
    # Single instance of Players, for all sounds.
    players = Players()

    def __init__(self):
        self._SAMPLE_RATE = 44100
        self._BYTES_PER_SAMPLE = 2
        self._CHANNELS = 1
        self._length = 0
        self.gain = 1
        self.loops = 1
        self.duration = 0
        self.stop_play_mutex = RLock()
        self.play_state = STOP
        self.state_change = STOP
        self.do_stop = False
        self.cv_play_state = Condition()
        self.do_play = Event()
        self.flush_done = Event()
        self.start_time = None
        self.play_thread = Thread(target=self.__play_thread)
        self.play_thread.daemon = True
        self.play_thread.start()

    def length(self):
        '''Returns the length of the sound in seconds'''
        return self._length

    def is_playing(self):
        return self.play_state != STOP

    def wait(self, timeout=None):
        '''Wait until the sound has finished playing.'''
        self.__wait_for_state(STOP)
        if self.start_time:
            if self.duration == None:
                total_time = self._length
            else:
                total_time = self.duration
            total_time *= self.loops
            wait_time = total_time - (time.time() - self.start_time)
            if wait_time > 0:
                time.sleep(wait_time)
        return self
            

    def stop(self):
        if self.play_state != STOP:
            with self.stop_play_mutex:
                self.do_stop = True
                self.players.remove(self)
                self.flush_done.set()
                self.__wait_for_state(STOP)
        return self

    def play(self, loops=1, duration=None):
        if duration and duration < 0:
            raise ValueError("duration must be a positive number")
        with self.stop_play_mutex:
            self.stop()
            self.loops = loops
            self.duration = duration
            self.play_q = Queue()
            self.players.add(self)
            self.start_time = None
            self.do_play.set()
            self.__wait_for_state(PLAY)
        return self

    def __wait_for_state(self, state):
        with self.cv_play_state:
            self.cv_play_state.wait_for(lambda:self.play_state == state)

    def __set_state(self, state):
        with self.cv_play_state:
            self.play_state = state
            self.cv_play_state.notify()
    
    def __play_thread(self):
        while True:
            self.do_play.wait()
            self.__set_state(PLAY)

            chunk = self._chunker(self.loops, self.duration)
            count = 0

            self.do_stop = False
            while not self.do_stop:
                try:
                    self.play_q.put((count, next(chunk), self.volume/100), timeout=0.01)
                except Full:
                    pass
                except StopIteration:
                    self.play_q.put((-1, None, None)) # EOF
                    break
                count += 1

            self.__set_state(FLUSH)
            self.flush_done.wait()

            self.do_play.clear()
            self.flush_done.clear()
            self.__set_state(STOP)

    def _time_to_bytes(self, duration):
        if duration == None:
            return None
        samples = duration * self._SAMPLE_RATE
        return samples * self._BYTES_PER_SAMPLE

    @property
    def volume(self):
        return round(self.gain*100)

    @volume.setter
    def volume(self, level):
        if level < 0:
            raise ValueError("level must be a positive number")
        self.gain = level/100

    # dummy chunking function
    def _chunker(self, loops, duration):
        return bytes(CHUNK_BYTES)

class Sound(BaseSound):
    def __init__(self, filename):
        '''A playable sound backed by the sound file `filename` on disk.
        
        Throws `IOError` if the sound file cannot be read.
        '''
        super().__init__()

        self.bytes = None
        if isinstance(filename, bytes):
            data = filename 
            self.file_opener = partial(io.BytesIO, data)
            byte_length = len(data)

        else:
            # Is it a file?  Not a definitive test here, but used as a courtesy to
            # give a better error when the filename is wrong.
            if not os.path.isfile(filename):
                raise IOError("Sound file '{}' cannot be found".format(filename))

            # Create cached file
            if not os.path.isdir(SOUND_CACHE):
                os.makedirs(SOUND_CACHE)
        
            _, file_ext = os.path.splitext(filename)
            if file_ext != '.raw':
                # Use sox to convert sound file to raw cached sound
                elongated_file_name = re.sub('/', '_', filename)
                raw_name = os.path.join(SOUND_CACHE, elongated_file_name)

                # If cached file doesn't exist, create it using sox
                if not os.path.isfile(raw_name):
                    soxcmd = ['sox',
                        '-q',
                        filename,
                        '-L',
                        '-r44100',
                        '-b16',
                        '-c1',
                        '-traw',
                        raw_name]
                    shell_cmd(soxcmd)
                    # test error
                filename = raw_name

            self.file_opener = partial(open, filename, 'rb')

            byte_length = os.path.getsize(filename)

        self._length = round(byte_length / (self._SAMPLE_RATE * self._BYTES_PER_SAMPLE), 6)

    def _chunker(self, loops, duration):
        with self.file_opener() as f:
            duration_bytes = self._time_to_bytes(duration)
            leftover = b''
            for loop in reversed(range(loops)):
                f.seek(0)
                bytes_written = 0
                while duration_bytes == None or bytes_written < duration_bytes:
                    if leftover:
                        chunk = leftover + f.read(CHUNK_BYTES - len(leftover))
                        leftover = b''
                    else:
                        chunk = f.read(CHUNK_BYTES)
                    if chunk:
                        if len(chunk) < CHUNK_BYTES and loop > 0:
                            # Save partial chunk as leftovers
                            leftover = chunk
                            break
                        else:
                            # Pad silence, if we're on the last loop and it's not a full chunk
                            if loop == 0:
                                chunk = chunk + bytes(CHUNK_BYTES)[len(chunk):]
                            bytes_written += CHUNK_BYTES
                            yield chunk
                    else:
                        # EOF
                        break

class Note(BaseSound):
    def __init__(self, pitch):
        '''
        '''
        super().__init__()

        try:
            self.frequency = float(pitch)
        except ValueError:
            match = re.search('^([A-G])([b#]?)([0-9]?)$', pitch)
            if not match:
                raise ValueError("pitch parameter must be a frequency or note (e.g. 'A', 'B#', or 'Cb4'")
            note, semitone, octave = match.groups()

            if not semitone:
                semitone_adjust = 0
            elif semitone == 'b':
                semitone_adjust = -1
            else:
                semitone_adjust = 1

            if not octave:
                octave = 4
            octave = int(octave)

            half_step_map = {'C' : 0, 'D' : 2, 'E' : 4, 'F' : 5, 'G' : 7, 'A' : 9, 'B' : 11}
            half_steps = octave * 12 + half_step_map[note]

            half_steps += semitone_adjust

            # Adjust half steps relative to A4 440Hz
            half_steps -= 4 * 12 + 9

            self.frequency = 2 ** (half_steps / 12.0) * 440.0

    def play(self, duration=1):
        super().play(duration=duration)
        return self

    def _chunker(self, loops, duration):
        if duration == None:
            chunks = 999999999
        else:
            chunks = int((self._time_to_bytes(duration) * loops) / CHUNK_BYTES)
        for chunk in range(chunks):
            yield mixer.note(chunk, float(self.frequency))

class Speech(Sound):
    def __init__(self, text, espeak_options=''):
        '''
        '''
        wav_fd, wav_name = tempfile.mkstemp(suffix='.wav')
        os.system('espeak {} -w {} "{}"'.format(espeak_options, wav_name, text))
        os.close(wav_fd)
        self.wav_name = wav_name
        super().__init__(wav_name)

    def __del__(self):
        os.remove(self.wav_name)
        
__all__ = ['Sound', 'Note', 'Speech', 'master_volume']
