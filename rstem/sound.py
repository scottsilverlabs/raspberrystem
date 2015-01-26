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

class Sound(object):
    def __init__(self, filename):
        '''A playable sound backed by the sound file `filename` on disk.
        
        Throws `IOError` if the sound file cannot be read.
        '''
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

        self.mutex = Lock()
        self.sox = None

    def length(self):
        '''Returns the length in seconds of the Sound'''
        return self._length

    def play(self, loop=1, duration=None):
        args = ['-q', [self.filename], 'repeat {}'.format(loop-1)]
        if duration != None:
            args += 'trim {}'.format(duration)
        self.sox = Sox(*args, play=True)

    def is_playing(self):
        with self.mutex:
            if not self.sox:
                return False
            _is_playing = self.sox.poll() == None
            if not _is_playing:
                self.sox = None
            return _is_playing

__all__ = ['Sound']
