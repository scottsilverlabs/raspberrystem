#!/usr/bin/env python3
#We need GPIO control and time so import those
import time
import RPi.GPIO as GPIO

#Lets make it a function so we can easily take many measurements
#We are going to need to know the send pin, the receive pin, and the number of samples
#We should also make an optional timeout argument to throw an error if it takes to long
def capRead(send, rec, samples, timeout=1000000):
#	Lets initialize the timing variable "t" and set the send pin to output 
	t = 0
	GPIO.setup(send, GPIO.OUT)

#	We are going to need to repeat sampling for the number of requested samples
	for samp in range(0,samples):
#		Now the magic happens, to clear any built up charge we need to set the send
#		and receive pins to OUTPUT and set them to LOW
		GPIO.output(send, False)			
		GPIO.setup(rec, GPIO.OUT)
		GPIO.output(rec, False)

#		Now we need to set our receive pin to INPUT and the send pin to HIGH
		GPIO.setup(rec, GPIO.IN)		
		GPIO.output(send, True)

#		Now we need to time how long it takes the receive pin to go HIGH which will
#		depend on the value of the resistor used and the capacitance that pin is seeing,
#		we also want to stop and return an error if we exceed timeout 		
		while((not GPIO.input(rec)) and (t < timeout)):
			t = t + 1
		if t >= timeout:
			print("Timed out!")
			return -1
#		Now we want to measure how long it takes the charged receive pin to discharge through the resistor
# 		so we need first charge the receive pin
		GPIO.setup(rec, GPIO.IN, pull_up_down = GPIO.PUD_UP)
		GPIO.setup(rec, GPIO.IN, pull_up_down = GPIO.PUD_OFF)

#		Now we set the send pin to LOW
		GPIO.output(send, False)
		
#		And time how long it take the receive pin to discharge
		while((GPIO.input(rec)) and (t < timeout)):
			t = t + 1

#	Then simply return the average of the samples
	return t/samples

#Lets make a little test program, this first "if statement" just tell python to run the following code only
#if this script is called directly, not if it is imported into another script, very useful for testing modules
if __name__ == "__main__":
#	Who needs warnings...
	GPIO.setwarnings(False)

#	This just tells RPi.GPIO what pin naming scheme your using, the pins on our cases are all labled using this mode
	GPIO.setmode(GPIO.BCM)

#	Use your favorite pins
	send = 22
	rec = 4

#	Lets continually print using the send and rec pins at 100 samples (press Ctrl-C to terminate)
	while True:
		print(capRead(send, rec, 100))
 
