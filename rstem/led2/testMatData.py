#!/usr/bin/env python

import accel_server as SPI
from time import sleep
SPI.initSPI(500000)
noError = 1;
its = int(0)
for i in range(0,16):
	for j in range(0,4):
		r = SPI.write(0xFF)
		if r != (i&7)*16+(i&7):
			print "Failed in initialization"
while noError:
	for x in range(0,16):
		for y in range(0,4):
			r = SPI.write(0x00)
			if r != (255):
				noError = 0
				print "Was %i expecting %i (Iterations: %i)" % (r,255,its)
	for x in range(0,16):
		for y in range(0,4):
			r=SPI.write(0xFF)
			if r != 0:
				print "Was %i expecting %i (Iterations: %i)" % (r,0,its)
	its = its + 1
