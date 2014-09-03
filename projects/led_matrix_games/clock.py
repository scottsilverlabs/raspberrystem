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

from rstem import led_matrix, button
import RPi.GPIO as GPIO
import time
import sys

# initialize led matrix
#led_matrix.init_grid()
led_matrix.init_matrices([(0,8),(8,8),(8,0),(0,0)])

A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(START, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SELECT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# notify menu we are ready for the led matrix
print("READY")
sys.stdout.flush()

while True:
    if GPIO.input(START) == 0 or GPIO.input(SELECT) == 0:
        button.cleanup()
        led_matrix.cleanup()
        sys.exit(0)
        
    hour = time.strftime("%I", time.localtime())
    hour = led_matrix.LEDText(hour)
    minute = time.strftime("%M", time.localtime())
    minute = led_matrix.LEDText(minute)
    
    led_matrix.erase()
    led_matrix.text(hour)
    led_matrix.text(minute, (hour.width + 2, 0))
    led_matrix.show()
