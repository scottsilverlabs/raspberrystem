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
import math
from rstem import led

def new_vector(ball, direction, speed, time, width=8.0, height=8.0):
    x, y = ball
    distance = speed * time
    x = x + distance * math.cos(math.radians(direction))
    y = y + distance * math.sin(math.radians(direction))
    if x >= width:
        x = 2 * width - x
        direction = 180 - direction
    if x < 0:
        x = -x
        direction = 180 - direction
    if y >= height:
        y = 2 * height - y
        direction = -direction
    if y < 0:
        y = - y
        direction = -direction
    return ((x, y), direction)
    
ball = (0.0, 0.0)
direction = 70.0
speed = 100.0
period = 0.02
dimensions = (1,1)
width=led.width()
height=led.height()
tick = 0
while True:
    led.erase()
    led.rect(tuple(int(x) for x in ball), dimensions)
    led.show()
    time.sleep(period);
    ball, direction = new_vector(ball, direction, speed, period, width=width, height=height)
    if tick % 100 == 0:
        direction += 1000
    tick += 1

