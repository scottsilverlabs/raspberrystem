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
from rstem import led2
led = led2

def width():
	return 8

def height():
	return 8
led.init_matrices([(0,0,90)])
led.width = width
led.height = height

x = 0.0
y = 0.0
xdist = 0.1
ydist = 0.5
period = 0.01
while True:
    # Draw the ball (which is just a point)
    led.fill(0)
    if (0 <= int(x) < 8 and 0 <= int(y) < 8):
        led.point(int(x), int(y))
    led.show()

    # Move the point to a new position.  If it hits a wall, reverse the
    # direction of the ball.
    x, y = (x+xdist, y+ydist)
    if x >= led.width() or x < 0:
        xdist = - xdist
    if y >= led.height() or y < 0:
        ydist = - ydist

    time.sleep(period)

