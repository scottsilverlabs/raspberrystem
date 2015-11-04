#
# Copyright (c) 2015, Scott Silver Labs, LLC.
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
This module provides function to control a Minecraft Pi player.
'''

import os
import time
from subprocess import call, Popen, PIPE
from functools import partial

shcall = partial(call, shell=True)
shopen = partial(Popen, stdin=PIPE, stderr=PIPE, stdout=PIPE, close_fds=True, shell=True)

MINECRAFT_WIN_NAME = 'Minecraft - Pi edition'
XDOTOOL_CMD = "DISPLAY=:0 xdotool search --name '{:s}'".format(MINECRAFT_WIN_NAME)

def show(show=True):
    ret = shcall(XDOTOOL_CMD + " {:s} --sync".format("windowmap" if show else "windowunmap"))
    if ret:
        raise IOError('Could not show/hide minecraft window.  Is it running?')

def hide():
    show(show=False)

__all__ = ['show']
