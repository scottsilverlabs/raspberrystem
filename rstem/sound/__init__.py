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
This module provides interfaces to the RaspberrySTEM CREATOR Kit speaker.

Additionally, it can be used for any audio out over the analog audio jack.
'''

import os
import sys
import time
import re
import io
import select
from functools import partial
from . import soundutil     # c extension
import tempfile
from threading import RLock, Thread, Condition, Event
from queue import Queue, Full, Empty
from subprocess import call, check_output
from struct import pack, unpack
import socket

'''
    Future Sound class member function:
        def seek(self, position, absolute=False, percentage=False)
            - relative +/- seconds
            - absolute +/- seconds (-negative seconds from end)
            - absolute percentage
            - returns previous position, in seconds
'''

STOP, PLAY, FLUSH, STOPPING = range(4)
CHUNK_BYTES = 1024
SOUND_CACHE = '/home/pi/.rstem_sounds'
SOUND_DIR = '/opt/raspberrystem/sounds'
MIXER_EXE_BASENAME = 'rstem_mixer'
MIXER_EXE_DIRNAME = '/opt/raspberrystem/bin'
MIXER_EXE = os.path.join(MIXER_EXE_DIRNAME, MIXER_EXE_BASENAME)
SERVER_PORT = 8888

def shell_cmd(cmd):
    with open(os.devnull, "w") as devnull:
        call(cmd, stdout=devnull, stderr=devnull, shell=True)

def start_server():
    # start server (if it is not already running)
    shell_cmd('pgrep -c {} || {} &'.format(MIXER_EXE_BASENAME, MIXER_EXE))

    # Wait until server is up
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for tries in range(30):
        try:
            sock.connect(("localhost", SERVER_PORT))
        except socket.error:
            pass
        else:
            sock.close()
            break
        time.sleep(0.1)

def sound_dir():
    return SOUND_DIR

def master_volume(level):
    if level < 0 or level > 100:
        raise ValueError("level must be between 0 and 100.")

    shell_cmd('amixer sset PCM {}%'.format(int(level)))

def clean_close(sock):
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except socket.error:
        pass
    try:
        sock.close()
    except socket.error:
        pass

class BaseSound(object):
    # Default master volume
    master_volume(100)
    start_server()

    def __init__(self):
        self._SAMPLE_RATE = 44100
        self._BYTES_PER_SAMPLE = 2
        self._CHANNELS = 1
        self._length = 0
        self.gain = 1
        self.internal_gain = 1
        self.start_time = None
        self.stop_play_mutex = RLock()
        self.stopped = Event()
        self.stopped.set()

        # Create play msg queue, with added member function that allows a
        # get_nowait() that can return empty if nothing is available.
        self.play_msg = Queue()
        def get_nowait_noempty():
            try:
                return self.play_msg.get_nowait()
            except Empty:
                return (None, None)
        self.play_msg.get_nowait_noempty = get_nowait_noempty

        self.play_count = 0
        self.play_thread = Thread(target=self.__play_thread)
        self.play_thread.daemon = True
        self.play_thread.start()

    def length(self):
        '''Returns the length of the sound in seconds'''
        return self._length

    def is_playing(self):
        '''Returns `True` if the sound is currently playing'''
        return not self.stopped.is_set()

    def wait(self, timeout=None):
        '''Wait until the sound has finished playing.
        
        If timeout is given (seconds), will return early (after the timeout
        time) even if the sound is not finished playing.

        Returns itself, so this function can be chained.
        '''
        assert self.play_thread.is_alive()
        self.stopped.wait(timeout)
        return self

    def stop(self):
        '''Immediately stop the sound from playing.

        Does nothing if the sound is not currently playing.

        Returns itself, so this function can be chained.
        '''
        assert self.play_thread.is_alive()
        with self.stop_play_mutex:
            self.play_msg.put((STOP, None))
            self.wait()
        return self

    def play(self, loops=1, duration=None):
        '''Starts playing the sound.

        This function starts playing the sound, and returns immediately - the
        sound plays in the background.  To wait for the sound, use `wait()`.
        Because sound functions can be chained, to create, play and wait for a
        sound to complete can be done in one compound command.  For example:

            Sound('mysound.wav').play().wait()

        `loops` is the number of times the sound should be played.  `duration`
        is the length of the sound to play (or `None` to play forever, or until
        the sound ends).

        Returns itself, so this function can be chained.
        '''
        assert self.play_thread.is_alive()
        if duration and duration < 0:
            raise ValueError("duration must be a positive number")
        with self.stop_play_mutex:
            self.stop()
            self.end_time = time.time() 
            previous_play_count = self.play_count
            self.play_msg.put((PLAY, (loops, duration)))

            # Wait until we know the play has started (i.e., the state ===
            # PLAY).  Ugly (polled), but simple.
            while previous_play_count == self.play_count:
                time.sleep(0.001)
        return self

    def __play_thread(self):
        state = STOP
        while True:
            if state == STOP:
                msg, payload = self.play_msg.get()
                if msg == PLAY:
                    self.stopped.clear()
                    self.play_count += 1
                    loops, duration = payload
                    chunk = self._chunker(loops, duration)
                    count = 0
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(("localhost", SERVER_PORT))
                    state = PLAY

            elif state == PLAY:
                msg, payload = self.play_msg.get_nowait_noempty()
                if msg == STOP:
                    state = STOPPING
                else:
                    try:
                        try:
                            header = pack('if', count, self.gain)
                            sock.send(header + next(chunk))
                            count += 1
                        except StopIteration:
                            header = pack('if', -1, 0)
                            sock.send(header)
                            state = FLUSH

                        readable, writable, exceptional = select.select([sock], [], [sock], 0)
                        if readable:
                            c = sock.recv(1)
                            eof = not c or ord(c)
                            if eof:
                                state = FLUSH
                        if exceptional:
                            state = FLUSH
                    except socket.error:
                        state = STOPPING

                # Throttle
                time.sleep(0.005)

            elif state == FLUSH:
                msg, payload = self.play_msg.get_nowait_noempty()
                if msg == STOP:
                    state = STOPPING
                else:
                    # Server will play sound to end and close socket.
                    eof_ack = sock.recv(1)
                    if not eof_ack:
                        state = STOPPING

                # Throttle
                time.sleep(0.005)

            elif state == STOPPING:
                clean_close(sock)
                self.stopped.set()
                state = STOP

    def _time_to_bytes(self, duration):
        if duration == None:
            return None
        samples = duration * self._SAMPLE_RATE
        return samples * self._BYTES_PER_SAMPLE

    @property
    def volume(self):
        '''The volume of the sound object
        
        Each sound object has an volume (idpendent of the `master_volume()`),
        between 0 (muted) and 100 (loudest).

        The volume is readable/writeable.
        '''
        return round(self.gain * self.internal_gain * 100)

    @volume.setter
    def volume(self, level):
        if level < 0:
            raise ValueError("level must be a positive number")
        self.gain = (level/100)/self.internal_gain

    # dummy chunking function
    def _chunker(self, loops, duration):
        return bytes(CHUNK_BYTES)

class Sound(BaseSound):
    '''
    A Sound object, that plays sounds read in from sound files.

    In addition to the Sound object, this module provides some useful global
    functions:

        master_volume(level):
            Sets the master volume (between 0 and 100) 
            of the audio out.

        sound_dir():
            Returns the sounds dir, where all sound 
            files are stored.
    '''
    
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
            # normalize path, raltive to SOUND_DIR
            try:
                filename = os.path.normpath(os.path.join(SOUND_DIR, filename))
            except:
                raise ValueError("Filename '{}' is not valid".format(filename))

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
                    soxcmd = 'sox -q {} -L -r44100 -b16 -c1 -traw {}'.format(filename, raw_name)
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
    '''A sine wave sound object. '''

    def __init__(self, pitch):
        '''Create a sound object that is a sine wave of the given `pitch`.
        '''
        super().__init__()

        A4_frequency = 440
        A6_frequency = A4_frequency * 2 * 2

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

            self.frequency = 2 ** (half_steps / 12.0) * A4_frequency

        # Simple bass boost: scale up the volume of lower frequency notes.  For
        # each octave below a 'A6', double the volume
        if self.frequency < A6_frequency:
            self.internal_gain = A6_frequency / self.frequency

    def play(self, duration=1):
        super().play(duration=duration)
        return self

    def _chunker(self, loops, duration):
        if duration == None:
            chunks = 999999999
        else:
            chunks = int((self._time_to_bytes(duration) * loops) / CHUNK_BYTES)
        for chunk in range(chunks):
            yield soundutil.note(chunk, float(self.frequency))

class Speech(Sound):
    '''A text-to-speech sound object.'''

    def __init__(self, text, espeak_options=''):
        '''Create a sound object that is text-to-speech of the given `text`.

        The sound is created using the espeak engine (an external program).
        Command line options to espeak can be added using `espeak_options`.
        '''
        wav_fd, wav_name = tempfile.mkstemp(suffix='.wav')
        os.system('espeak {} -w {} "{}"'.format(espeak_options, wav_name, text))
        os.close(wav_fd)
        self.wav_name = wav_name
        super().__init__(wav_name)

    def __del__(self):
        os.remove(self.wav_name)
        
__all__ = ['Sound', 'Note', 'Speech', 'master_volume' 'sound_dir']
