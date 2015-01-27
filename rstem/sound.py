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
This module provides interfaces to the buttons and switches in the Button RaspberrySTEM Cell.
'''

import os
import time
import re
from threading import Lock
from subprocess import Popen, PIPE

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


__all__ = ['Sound']
