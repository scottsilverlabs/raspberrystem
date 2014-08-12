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
#This project turns the pi into the user's very own mulimeter for capacitance
#all it requires is one capacitor of know or unknown value and one resistor of
#known value and it will measure the capacitance. Works really well on values on
#or above the order of uF.
#Need GPIOs, time, and natural log function
import RPi.GPIO as GPIO
import time
from numpy import log

GPIO.setmode(GPIO.BCM)

RESITANCE = 200000
OUT = 25
IN = 18

def measure(outPin, inPin, Resistance):
    #Clear charge
    GPIO.setup(inPin, GPIO.OUT)
    GPIO.setup(outPin, GPIO.OUT)
    GPIO.output(inPin, False)
    GPIO.output(outPin, False)

    #Set input and output
    GPIO.setup(inPin, GPIO.IN)
    GPIO.output(outPin, True)
    t1 = time.time()
    #Measure time
    while(not GPIO.input(inPin)):
        pass
    
    t2 = time.time()
    chargeTime = t2-t1
    #Calculate capacitance
    capacitance = -chargeTime/(log(1-1.3/3.3)*Resistance)
    return capacitance

#Print out some values
try:
    for x in range(100):
        print("Capacitance: %f uF" % (measure(OUT, IN, RESISTANCE)*10**6))
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
