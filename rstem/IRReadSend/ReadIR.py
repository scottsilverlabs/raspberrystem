#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import sys
pulses = []
lastEdge = 0
edge = 0

command  = [1066, 1126, 1123, 1129, 1099, 1127, 1113, 1126, 2233, 2269, 2217, 2238, 2258, 2232, 2231, 2250, 1136, 1104, 1122, 1135, 1120, 1109, 2232, 1125, 2238, 2234, 2269, 2219, 2235, 2250, 1136, 2227]

def readIR(channel):
	global pulses
	global edge
	global lastEdge
	edge = round(time.time()*1000000)
	pulses.append(edge - lastEdge)
	lastEdge = edge

def sendIR(command):
	for data in command:
		carrier = data
		while carrier > 0:
			GPIO.output(ledPin, True)
			GPIO.output(ledPin, False)
			carrier  = carrier - 1


GPIO.setmode(GPIO.BCM)
sensorPin = 23
ledPin = 18
GPIO.setup(sensorPin, GPIO.IN)
GPIO.setup(ledPin, GPIO.OUT)
GPIO.add_event_detect(23, GPIO.FALLING, callback=readIR)
while True:
	x = input("Enter any key for list: ")
	print(pulses)
	if x == "exit":
		GPIO.cleanup()
		sys.exit(0)
	if x == "send":
		sendIR(command)
