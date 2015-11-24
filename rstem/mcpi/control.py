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
from .vec3 import Vec3
from . import block
from math import atan2, degrees, sqrt, floor
import atexit

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
    uinput.BTN_LEFT,
    uinput.BTN_RIGHT,
    uinput.REL_X,
    uinput.REL_Y,
    ]
device = uinput.Device(keys)
time.sleep(0.5)

item_keys = [eval('uinput.KEY_{:d}'.format(item+1)) for item in range(8)]

MIN_DURATION_PRESS = 0.1

def show(show=True, hide_at_exit=False):
    ret = shcall(SHOW_WIN_CMD if show else HIDE_WIN_CMD)
    if ret:
        raise IOError('Could not show/hide minecraft window.  Is it running?')

    if hide_at_exit:
        atexit.register(hide)

def hide():
    show(show=False)

def key_release(key):
    key_press(key, release=True)

def key_press(key, duration=None, release=False, wait=True):
    if release:
        device.emit(key, 0)
    else:
        if not duration:
            device.emit(key, 1)
        else:
            if wait:
                device.emit(key, 1)
                time.sleep(duration)
                device.emit(key, 0)
            else:
                device.emit(key, 1)
                Timer(duration, key_release, args=[key]).start()

def backward(duration=None, release=False, wait=True):
    key_press(uinput.KEY_S, duration, release, wait)

def forward(duration=None, release=False, wait=True):
    key_press(uinput.KEY_W, duration, release, wait)

def left(duration=None, release=False, wait=True):
    key_press(uinput.KEY_A, duration, release, wait)

def right(duration=None, release=False, wait=True):
    key_press(uinput.KEY_D, duration, release, wait)

def jump(duration=0.5, release=False, wait=True):
    key_press(uinput.KEY_SPACE, duration, release, wait)

def crouch(duration=None, release=False, wait=True):
    key_press(uinput.KEY_LEFTSHIFT, duration, release, wait)

def ascend(duration=None, release=False, wait=True):
    jump(duration, release, wait)

def descend(duration=None, release=False, wait=True):
    crouch(duration, release, wait)

def stop():
    for key in keys:
        key_release(key)

def smash(duration=MIN_DURATION_PRESS, release=False, wait=True):
    key_press(uinput.BTN_LEFT, duration, release, wait)

def place(duration=MIN_DURATION_PRESS, release=False, wait=True):
    key_press(uinput.BTN_RIGHT, duration, release, wait)

def hit(*args, **kwargs):
    place(*args, **kwargs)

def toggle_fly_mode():
    for i in range(2):
        jump(duration=MIN_DURATION_PRESS)
        time.sleep(MIN_DURATION_PRESS)

def item(choice):
    if not (1 <= choice <= 8):
        raise ValueError('choice must be from 1 to 8')
    key_press(item_keys[choice-1], duration=MIN_DURATION_PRESS)

def enter():
    key_press(uinput.KEY_ENTER, duration=MIN_DURATION_PRESS)

def inventory():
    key_press(uinput.KEY_E, duration=MIN_DURATION_PRESS)

def look(left=0, right=0, up=0, down=0, sync=False):
    device.emit(uinput.REL_X, int(right-left), syn=False)
    device.emit(uinput.REL_Y, int(down-up))
    if sync:
        # add throttling to prevent look() overruns
        time.sleep(0.2)

def _wait_until_stopped(mc):
    prev = None
    cur = mc.player.getPos()
    while cur != prev:
        prev = cur
        cur = mc.player.getPos()
        time.sleep(0.05)
    return cur

def _make_platform(mc, erase=False, height=58, half_width=3):
    mc.setBlocks(
        Vec3(-half_width-1, height+0, -half_width-1),
        Vec3(half_width+1, height+4, half_width+1),
        block.AIR if erase else block.STONE)
    mc.setBlocks(
        Vec3(-half_width, height+1, -half_width),
        Vec3(half_width, height+3, half_width),
        block.AIR if erase else block.COBWEB)

    return Vec3(0, height+1, 0)

def get_heading(mc):
    original_pos = mc.player.getPos()
    center_of_platform = _make_platform(mc)
    mc.player.setPos(center_of_platform)
    forward(0.1)
    end = _wait_until_stopped(mc)
    _make_platform(mc, erase=True)

    mc.player.setPos(original_pos)

    angle_to_z = degrees(atan2((end.x - center_of_platform.x),(end.z - center_of_platform.z)))
    return angle_to_z

def _circle(mc, origin, radius, blk):
    for delta_x in range(-int(radius), int(radius)+1):
        z_vector = Vec3(0, 0, floor(sqrt(radius**2 - delta_x**2)))
        v = origin + Vec3(delta_x,0,0)
        mc.setBlocks(v - z_vector, v + z_vector, blk)

def _sphere(mc, origin, radius, blk):
    for delta_y in range(-int(radius), int(radius)+1):
        _circle(mc, origin + Vec3(0,delta_y,0), sqrt(radius**2 - delta_y**2), blk)

def get_direction(mc):
    origin = Vec3(0,58,0)
    radius = 3.9
    box_offset = Vec3(radius+1, radius+1, radius+1)
    mc.setBlocks(origin - box_offset, origin + box_offset, block.GLASS)
    _sphere(mc, origin, radius, block.AIR)
    mc.setBlocks(origin, origin + Vec3(0, radius, 0), block.AIR)
    mc.setBlock(origin + Vec3(0, -2, 0), block.STONE)

    pos = mc.player.getPos()
    mc.player.setTilePos(origin + Vec3(0, -1, 0))
    tries = 3
    while tries:
        time.sleep(0.1)
        hit(0.2)
        hits = mc.events.pollBlockHits()
        if hits:
            break
        look(left=1)
        tries -= 1
    mc.player.setPos(pos)
    mc.setBlocks(origin - box_offset, origin + box_offset, block.AIR)
    hit_pos = hits[0].pos
    direction = hit_pos - origin
    theta = degrees(atan2(direction.x, direction.z))
    phi = degrees(atan2(direction.y, sqrt(direction.z**2 + direction.x**2)))
    return (theta, phi)

__all__ = [
    'show',
    'hide',
    ]
