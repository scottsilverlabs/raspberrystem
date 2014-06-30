#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

led = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(led, GPIO.OUT)

for x in range(0,10):
	GPIO.output(led, True)
	time.sleep(1)
	GPIO.output(led, False)
	time.sleep(1)
GPIO.cleanup()
