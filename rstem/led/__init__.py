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
import time
import os
import sys
import fcntl
from led_server import LedServer
from led_cal import LedCal
from led_draw import LedDraw
from subprocess import *

def _init_module():
    server = LedServer()
    cal = LedCal(server)
    draw = LedDraw(server, cal)
    draw.erase()
    return server, cal, draw

server, cal, draw = _init_module()
name_mappings = [
    (draw,  'show'),
    (draw,  'rect'),
    (draw,  'line'),
    (draw,  'point'),
    (draw,  'bound'),
    (draw,  'erase'),
    (cal,   'v'),
    (cal,   'h'),
    (cal,   'recalibrate'),
    (cal,   'width',    'get_fb_width'),
    (cal,   'height',   'get_fb_height'),
    ]
    
for m in name_mappings:
    if len(m) == 2:
        module, exported_name = m
        name_in_module = exported_name
    else:
        module, exported_name, name_in_module = m
    globals()[exported_name] = getattr(module, name_in_module)

def _main():
    while 1:
        for i in range(8):
            for j in range(8):
                led.point(x, y)
                led.show()
                time.sleep(0.5);
                led.point(x, y, color=0)

if __name__ == "__main__":
    _main()

