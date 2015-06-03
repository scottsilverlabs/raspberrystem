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
import time
import re
from . import mixer     # c extension
import tempfile
from threading import RLock, Thread, Condition
from queue import PriorityQueue, Empty
from subprocess import Popen, PIPE

'''
    Future Sound class member function:
        def seek(self, position, absolute=False, percentage=False)
            - relative +/- seconds
            - absolute +/- seconds (-negative seconds from end)
            - absolute percentage
            - returns previous position, in seconds
'''
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
        chunks = 0
        while True:
            msgs = []
            with self.mutex:
                # For each player, get an audio buffer.
                for sound in frozenset(self.players):
                    priority, msg = sound.play_q.get()
                    if msg:
                        msgs.append(msg + (sound,))
                    else:
                        # No chunk means this is a STOP or EOF message
                        if priority < 0:
                            # We just got A high priority STOP message - flush the
                            # queue unitl we hit EOF.
                            while True:
                                try:
                                    sound.play_q.get_nowait()
                                    print("FLUSH")
                                    sound.play_q.task_done()
                                except Empty:
                                    break
                        self.remove(sound)
                        sound.play_q.task_done()
                        print("EOF")
            if msgs:
                chunk, gain, sound = msgs[0]
                mixer.play(chunk)
                sound.play_q.task_done()
                print(chunks, len(chunk), time.time())
                chunks += 1
            else:
                time.sleep(0.01)

class Sox(Popen):
    def __init__(self, *args, play=False):
        fullcmd = ['play' if play else 'sox']
        # split args by whitespace and flatten.
        for arg in args:
            if isinstance(arg, str):
                fullcmd += arg.split()
            else:
                fullcmd += arg
        super().__init__(fullcmd, stdout=PIPE, stderr=PIPE)

class SoxPlay(Sox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, play=True, **kwargs)

class BaseSound(object):
    # Single instance of Players, for all sounds.
    players = Players()

    def __init__(self):
        self._length = 0
        self.stop_play_mutex = RLock()
        self.sox = None
        self.play_q = PriorityQueue()
        self.stopped = False
        self.playing = False
        self.cv_playing = Condition()
        self.play_thread = Thread(target=self._play_thread)
        self.play_thread.daemon = True
        self.play_thread.start()

    def length(self):
        '''Returns the length in seconds of the sound'''
        return self._length

    def is_playing(self):
        return self.playing

    def wait(self, timeout=None):
        '''Wait until the sound has finished playing.'''
        print("wait start")
        with self.cv_playing:
            self.cv_playing.wait_for(lambda:not self.playing)
        print("wait end")

    def stop(self):
        if self.playing:
            with self.stop_play_mutex:
                self.play_q.put((-1, None))
                self.stopped = True
                with self.cv_playing:
                    self.cv_playing.wait_for(lambda:not self.playing)

    def play(self, loops=1, duration=None):
        with self.stop_play_mutex:
            self.stop()
            self.loops = loops
            self.duration = duration
            self.players.add(self)
            with self.cv_playing:
                self.playing = True
                self.cv_playing.notify()

    def _play_thread(self):
        while True:
            self.stopped = False
            with self.cv_playing:
                self.cv_playing.wait_for(lambda:self.playing)
            print("_play_thread: ", time.time())
            chunk = self._chunker(1024, self.loops, self.duration)
            chunks = 0
            print("_play_thread: ", time.time())
            try:
                while not self.stopped:
                    self.play_q.put((chunks, (next(chunk), 1)), timeout=0.01)
                    chunks += 1
            except StopIteration:
                pass
            print("_play_thread: ", time.time())
            self.play_q.put((chunks + 1, None)) # EOF
            print("_play_thread: ", time.time())
            self.play_q.join()
            print("_play_thread: ", time.time())
            with self.cv_playing:
                self.playing = False
                self.cv_playing.notify()
            print("_play_thread: ", time.time())

    # dummy chunking function
    def _chunker(chunk_size):
        return bytes(1024)

class Sound(BaseSound):
    def __init__(self, filename):
        '''A playable sound backed by the sound file `filename` on disk.
        
        Throws `IOError` if the sound file cannot be read.
        '''
        super().__init__()

        self.filename = filename

        # Is it a file?  Not a definitive test here, but used as a courtesy to
        # give a better error when the filename is wrong.
        if not os.path.isfile(filename):
            raise IOError("Sound file '{}' cannot be found".format(filename))

        out, err = Sox([filename], '-n stat').communicate()
        matches = (re.search('^Length.*?([^ ]+)$', line) for line in err.decode().splitlines())
        try:
            firstmatch = [match for match in matches if match][0]
            self._length = float(firstmatch.group(1))
        except IndexError:
            raise IOError("Sox could not get sound file's length")

    def _chunker(self, chunk_size, loops, duration):
        with open(self.filename, "rb") as f:
            chunks = 0
            while True:
                chunks += 1
                if duration != None and chunks * chunk_size / 44100 > duration:
                    break
                chunk = f.read(chunk_size)
                if chunk:
                    yield chunk
                else:
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
        with self.mutex:
            self._stop()
            duration = duration if duration else 0
            args = ['-q -n synth {} sine {} gain 20'.format(duration, self.frequency)]
            self.sox = SoxPlay(*args)
        return self

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
        
__all__ = ['Sound', 'Note', 'Speech']
