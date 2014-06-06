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
from rstem import led
from rstem import accel
from rstem import gpio

POLL_PERIOD=0.010
SHOOT=2
LEFT=3
DOWN=4
UP=14
RIGHT=15

for g in [SHOOT, LEFT, DOWN, UP, RIGHT]:
    gpio.configure(g, gpio.INPUT)

x1, y1 = 5, 5
x2, y2 = 7, 7
use2 = False
while True:
    clicks = gpio.was_clicked()
    if LEFT in clicks:
        if not use2:
            x1 -= 1
        else:
            x2 -= 1
    if RIGHT in clicks:
        if not use2:
            x1 += 1
        else:
            x2 += 1
    if DOWN in clicks:
        if not use2:
            y1 -= 1
        else:
            y2 -= 1
    if UP in clicks:
        if not use2:
            y1 += 1
        else:
            y2 += 1
    if SHOOT in clicks:
        use2 = not use2
    led.erase()
    color1 = 3 if not use2 else 1
    color2 = 3 if use2 else 1
    led.point(x1, y1, color=color1)
    led.point(x2, y2, color=color2)
    led.show()
    time.sleep(POLL_PERIOD)
    
