#!/usr/bin/env python3

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
from rstem import led_matrix, accel
import time

accel.init(1)
led_matrix.init_grid()

x, y = (3, 3)
while True:
    x_angle, y_angle, z_angle = accel.angles()
    
    x -= min(2, int(x_angle/4.0))
    x = max(0, min(7, x))
    y += min(2, int(y_angle/4.0))
    y = max(0, min(7, y))
    
    led_matrix.erase()
    led_matrix.point(x, y)
    led_matrix.show()
    
    time.sleep(.1)


