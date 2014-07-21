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

WIDTH=led.width()
HEIGHT=led.height()

for x in range(WIDTH):
    for y in range(HEIGHT):
        for w in range(WIDTH-x):
            for h in range(HEIGHT-y):
                led.erase()
                led.rect((x,y), (w,h))
                led.show()
                time.sleep(0.01);
