#!/usr/bin/env python

import led_matrix
from time import sleep
l = led_matrix.LEDMatrix(1,2)
while 1:
	for x in range(0,16):
		for y in range(0,8):
			for destx in range(0,16):
				for desty in range(0,8):
					for col in range(0,16):
						l.line((x,y),(destx,desty),col)
						l.show()
#						sleep(1.0/4.0)
					for col in range(0,16):
						l.line((x,y),(destx,desty),15-col)
						l.show()
#	for y in range(0,8):
#		l.line((0,y),(15,y),0)
#		l.show()
#		sleep(1.0/4.0)
#		sleep(1.0)
#		l.erase()
#	for x in range(0,16):
#		for y in range(0,8):
#			l.point(x,y)
#			l.show()
#			l.erase()
