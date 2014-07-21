#!/usr/bin/env python

from rstem import led2
from time import sleep
led2.init_matrices([(0,0),(8,0)])
while 1:
	for x in range(0,16):
		for y in range(0,8):
			for destx in range(0,16):
				for desty in range(0,8):
					for col in range(0,16):
						led2.line((x,y),(destx,desty),col)
						led2.show()
#						sleep(1.0/4.0)
					for col in range(0,16):
						led2.line((x,y),(destx,desty),15-col)
						led2.show()
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
