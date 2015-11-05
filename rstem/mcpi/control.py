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
import uinput
from threading import Timer

shcall = partial(call, shell=True)
shopen = partial(Popen, stdin=PIPE, stderr=PIPE, stdout=PIPE, close_fds=True, shell=True)

MINECRAFT_WIN_NAME = 'Minecraft - Pi edition'
HIDE_WIN_CMD = "DISPLAY=:0 wmctrl -r '{:s}' -b add,hidden".format(MINECRAFT_WIN_NAME)
SHOW_WIN_CMD = "DISPLAY=:0 wmctrl -a '{:s}'".format(MINECRAFT_WIN_NAME)

keys = [
    uinput.KEY_W,
    uinput.KEY_A,
    uinput.KEY_S,
    uinput.KEY_D,
    uinput.KEY_E,
    uinput.KEY_1,
    uinput.KEY_2,
    uinput.KEY_3,
    uinput.KEY_4,
    uinput.KEY_5,
    uinput.KEY_6,
    uinput.KEY_7,
    uinput.KEY_8,
    uinput.KEY_SPACE,
    uinput.KEY_ENTER,
    uinput.KEY_LEFTSHIFT,
    ]
device = uinput.Device(keys)
time.sleep(0.5)

def show(show=True):
    ret = shcall(SHOW_WIN_CMD if show else HIDE_WIN_CMD)
    if ret:
        raise IOError('Could not show/hide minecraft window.  Is it running?')

def hide():
    show(show=False)

def key_press(key, duration=None):
    global device
    device.emit(key, 1)
    if duration != None:
        Timer(duration,device.emit,args=[key, 0]).start()

def backward(duration=None):
    key_press(uinput.KEY_S, duration)

def forward(duration=None):
    key_press(uinput.KEY_W, duration)

def left(duration=None):
    key_press(uinput.KEY_A, duration)

def right(duration=None):
    key_press(uinput.KEY_D, duration)

def jump(duration=None):
    key_press(uinput.KEY_SPACE, duration)

def crouch(duration=None):
    key_press(uinput.KEY_LEFTSHIFT, duration)

def ascend(duration=None):
    jump(duration)

def descend(duration=None):
    crouch(duration)

def stop(duration=None):
    for key in keys:
        device.emit(key, 0)
        

__all__ = [
    'show',
    'hide',
    ]
