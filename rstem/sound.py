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
import tempfile
from threading import Lock
from subprocess import Popen, PIPE

'''
    Future Sound class member function:
        def seek(self, position, absolute=False, percentage=False)
            - relative +/- seconds
            - absolute +/- seconds (-negative seconds from end)
            - absolute percentage
            - returns previous position, in seconds
'''

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
    def __init__(self):
        self._length = 0
        self.mutex = Lock()
        self.sox = None

    def length(self):
        '''Returns the length in seconds of the sound'''
        return self._length

    def is_playing(self):
        with self.mutex:
            if not self.sox:
                return False
            playing = self.sox.poll() == None
            if not playing:
                self.sox = None
            return playing

    def wait(self):
        '''Wait until the sound has finished playing.'''
        with self.mutex:
            _sox = self.sox
            self.sox = None
        if _sox:
            _sox.wait()

    def _stop(self):
        if self.sox:
            self.sox.kill()
        self.sox = None

    def stop(self):
        with self.mutex:
            self._stop()

class Sound(BaseSound):
    def __init__(self, filename):
        '''A playable sound backed by the sound file `filename` on disk.
        
        Throws `IOError` if the sound file cannot be read.
        '''
        super().__init__()

        self.filename = filename

        # Is it a file?  Not a definitive test here, but used as a cuortesy to
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

    def play(self, loops=1, duration=None):
        with self.mutex:
            self._stop()
            args = ['-q', [self.filename]]
            if duration != None:
                if duration < 0:
                    duration = self._length + duration
                if duration >= 0 and duration <= self._length:
                    args += ['trim 0 {}'.format(duration)]
            args += ['repeat {}'.format(loops-1)]
            self.sox = SoxPlay(*args)

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
            args = ['-q -n synth {} sine {}'.format(duration, self.frequency)]
            self.sox = SoxPlay(*args)

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
