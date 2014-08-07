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
#In this project the user learns how to make a common cathode RGB LED cycle
#through the rainbow.
#Basic imports
import RPi.GPIO as GPIO
import time

#Pin declarations
redPin = 25
greenPin = 24
bluePin = 23

#Set mode and setup pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)

#Initialze PWM threads
red = GPIO.PWM(redPin, 100)
green = GPIO.PWM(greenPin, 100)
blue = GPIO.PWM(bluePin, 100)

#Start PWM threads, full red because we are starting at the low end of the spectrum
red.start(100)
green.start(0)
blue.start(0)

#Cycle through 10 times
for x in range(0,10):
#   Fade from full red to green
    red.ChangeDutyCycle(100)
    green.ChangeDutyCycle(0)
    blue.ChangeDutyCycle(0)
    for x in range(0,100):
        red.ChangeDutyCycle(100-x)
        green.ChangeDutyCycle(x)
        time.sleep(1.0/100.0)
#   Fade from full green to blue
    red.ChangeDutyCycle(0)
    green.ChangeDutyCycle(100)
    blue.ChangeDutyCycle(0)
    for x in range(0,100):
        green.ChangeDutyCycle(100-x)
        blue.ChangeDutyCycle(x)
        time.sleep(1.0/100.0)
#   Fade from full blue to red
    red.ChangeDutyCycle(0)
    green.ChangeDutyCycle(0)
    blue.ChangeDutyCycle(100)
    for x in range(0,100):
        blue.ChangeDutyCycle(100-x)
        red.ChangeDutyCycle(x)
        time.sleep(1.0/100.0)

#Stop threads and cleanup
red.stop()
blue.stop()
green.stop()
GPIO.cleanup()
