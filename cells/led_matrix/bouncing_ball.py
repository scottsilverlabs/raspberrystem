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

x = 0.0
y = 0.0
xdist = 0.1
ydist = 0.5
period = 0.01
while True:
    led.erase()
    led.point(int(x), int(y))
    led.show()
    time.sleep(period);
    x, y = (x+xdist, y+ydist)
    if (x >= led.width() or x < 0):
        xdist = - xdist
    if (y >= led.height() or y < 0):
        ydist = - ydist

