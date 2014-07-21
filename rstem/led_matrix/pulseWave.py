#!/usr/bin/env python

import led_matrix
from time import sleep
l = led_matrix.LEDMatrix(1,2)
while 1:
	for off in range(0,16):
		for x in range(0,16):
			l.line((x,0),(x,7),(x+off)&15)
		l.show()
