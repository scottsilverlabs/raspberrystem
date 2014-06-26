#!/usr/bin/env python
from __future__ import print_function
import time
import RPi.GPIO as GPIO

def capRead(send, rec, timeout=1000000):
	GPIO.setup(rec, GPIO.OUT)
	GPIO.output(rec, False)

	GPIO.setup(send, GPIO.OUT)
	GPIO.output(send, False)
	sleep(1.0/1000.0
	GPIO.setup(rec, GPIO.IN)
	GPIO.output(send, True)

	t1 = time.time()*1000000
	while(not GPIO.input(rec)):
		if(time.time()*1000000-t1>timeout):
			print("Timed out")
			break
	t2 = time.time()*1000000
	return int(t2-t1)

if __name__ == "__main__":
	f = open("capData.txt", "w")
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
	t1 = time.time()*1000000
	led = 22
	GPIO.setup(led, GPIO.OUT)
	while True:
		sum1 = 0
		sum2 = 0
		t1 = time.time()*1000000
		for y in range(0,1000):
			x = capRead(27,4,10000000)
			sum1 = sum1 + capRead(27,4)
		sum1 = sum1/1000.0
		GPIO.output(led, sum1>65)
		print(sum1)

def close():
	GPIO.cleanup()

import atexit
atexit.register(close)
