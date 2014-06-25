#!/usr/bin/env python
import time
import RPi.GPIO as GPIO

def capRead(send, rec, timeout=1000):
	GPIO.setup(send, GPIO.OUT)
	GPIO.output(send, False)
	GPIO.setup(rec, GPIO.IN)
	GPIO.output(send, True)
	t1 = time.time()*1000000
	while(not GPIO.input(rec)):
		timeout = timeout - 1
		if(timeout < 0):
			print "Timed out"
			break
	t2 = time.time()*1000000
	GPIO.setup(rec, GPIO.OUT)
	GPIO.output(rec, False)
	return int(t2-t1)

if __name__ == "__main__":
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	while True:
		sum1 = 0
		sum2 = 0
		for x in range(0,100):
			for y in range(0,100):
				sum1 = sum1 + capRead(25,24)
			sum1 = sum1/100.0
			sum2 = sum2 + sum1
		sum2 = sum2/100.0
		print sum2
		time.sleep(1)

def close():
	GPIO.cleanup()

import atexit
atexit.register(close)
