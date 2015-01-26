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
from subprocess import Popen, PIPE

class Sox(object):
    def __init__(self, *args, play=False):
        fullcmd = ['play' if play else 'sox']
        # split args by whitespace and flatten.
        for arg in args:
            if isinstance(arg, str):
                fullcmd += arg.split()
            else:
                fullcmd += arg
        self.proc = Popen(fullcmd, stdout=PIPE, stderr=PIPE)

    def wait(self):
        '''Wait for the sox command to complete

        Returns the output of the sox command.
        '''
        return self.proc.communicate()
    
    def kill(self):
        '''Kill a running sox process.'''
        self.proc.kill()
    
class Sound(object):
    def __init__(self, filename):
        self.filename = filename

        # Is it a file?  Not a definitive test here, but used as a cuortesy to
        # give a better error when the filename is wrong.
        if not os.path.isfile(filename):
            raise IOError("Sound file '{}' cannot be found".format(filename))

        out, err = Sox([filename], '-n stat').wait()
        matches = (re.search('^Length.*?([^ ]+)$', line) for line in err.decode().splitlines())
        try:
            firstmatch = [match for match in matches if match][0]
            self._length = float(firstmatch.group(1))
        except IndexError:
            raise IOError("Sox could not get sound file's length")

    def length(self):
        return self._length

__all__ = ['Sound']
