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
#In this project the user learns how to use PWM to fade an LED.
#Basic imports
import RPi.GPIO as GPIO
import time

#Set up mode and pin
GPIO.setmode(GPIO.BCM)
ledPin = 18
GPIO.setup(ledPin, GPIO.OUT)

#Start the PWM thread
led = GPIO.PWM(ledPin, 100)
led.start(0)

#Fade LED on then off
for dutyCycle in range(0, 100):
    led.ChangeDutyCycle(dutyCycle)
    time.sleep(0.01)
for dutyCycle in range(100, 0, -1):
    led.ChangeDutyCycle(dutyCycle)
    time.sleep(0.01)

#Stop the PWM thread and cleanup
led.stop()
GPIO.cleanup()
