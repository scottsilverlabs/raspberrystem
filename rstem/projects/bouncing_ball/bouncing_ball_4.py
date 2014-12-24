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
from itertools import cycle
from rstem import led
from rstem import accel

period = 0.01

class Ball():
    next_color = 1

    def __init__(self, position=(0,0), dist=(0.1,0.1)):
        self.x, self.y = position
        self.xdist, self.ydist = dist

        # Init the ball with a different color from the last one
        self.color = Ball.next_color
        Ball.next_color = (Ball.next_color % 15) + 1

    def draw(self):
        led.point(int(self.x), int(self.y))

    def move(self, angle=None):
        # Gravity
        if angle:
            xangle, yangle, zangle = angle
            self.xdist += self.xangle/90
            self.ydist += self.yangle/90

        # Move the point to a new position.  If it hits a wall, reverse the
        # direction of the ball.
        self.x, self.y = (self.x+self.xdist, self.y+self.ydist)
        if self.x >= led.width() or self.x < 0:
            self.xdist = - self.xdist
        if self.y >= led.height() or self.y < 0:
            self.ydist = - self.ydist


ball = Ball()
while True:
    # Draw the ball
    led.erase()
    ball.draw()
    led.show()

    # Move it (in the presense of gravity)
    ball.move(accel.get_angle())

    time.sleep(period)

