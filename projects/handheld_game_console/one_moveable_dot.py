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
LEFT=3
DOWN=4
UP=14
RIGHT=15

for g in [LEFT, DOWN, UP, RIGHT]:
    gpio.configure(g, gpio.INPUT)

x, y = 5, 5
while True:
    clicks = gpio.was_clicked()
    if LEFT in clicks:
            x -= 1
    if RIGHT in clicks:
            x += 1
    if DOWN in clicks:
            y -= 1
    if UP in clicks:
            y += 1
    led.erase()
    led.point(x, y)
    led.show()
    time.sleep(POLL_PERIOD)
    
