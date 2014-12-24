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
import RPi.GPIO as GPIO

#Lets make it a function so we can easily take many measurements
#We are going to need to know the send pin, the receive pin, and the number of samples
#We should also make an optional timeout argument to throw an error if it takes to long
def capRead(send, rec, samples, timeout=1000000):
    #Lets initialize the timing variable "t" and set the send pin to output 
    t = 0
    GPIO.setup(send, GPIO.OUT)

    #We are going to need to repeat sampling for the number of requested samples
    for samp in range(0,samples):
        #Now the magic happens, to clear any built up charge we need to set the send
        #and receive pins to OUTPUT and set them to LOW
        GPIO.output(send, False)            
        GPIO.setup(rec, GPIO.OUT)
        GPIO.output(rec, False)

        #Now we need to set our receive pin to INPUT and the send pin to HIGH
        GPIO.setup(rec, GPIO.IN)        
        GPIO.output(send, True)

        #Now we need to time how long it takes the receive pin to go HIGH which will
        #depend on the value of the resistor used and the capacitance that pin is seeing,
        #we also want to stop and return an error if we exceed timeout         
        while((not GPIO.input(rec)) and (t < timeout)):
            t = t + 1
        if t >= timeout:
            print("Timed out!")
            return -1
        #Now we want to measure how long it takes the charged receive pin to discharge through the resistor
        #so we need first charge the receive pin
        GPIO.setup(rec, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(rec, GPIO.IN, pull_up_down = GPIO.PUD_OFF)

        #Now we set the send pin to LOW
        GPIO.output(send, False)
        
        #And time how long it take the receive pin to discharge
        while((GPIO.input(rec)) and (t < timeout)):
            t = t + 1

    #Then simply return the average of the samples
    return t/samples

    #This just tells RPi.GPIO what pin naming scheme your using, the pins on our cases are all labled using this mode
    GPIO.setmode(GPIO.BCM)

    #Use your favorite pins
    send = 22
    rec = 4

    #Lets print 100 measurements using the send and rec pins at 100 samples (press Ctrl-C to terminate)
    for x in range(100):
        print(capRead(send, rec, 100))