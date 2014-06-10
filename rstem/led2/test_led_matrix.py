#!/usr/bin/env python
import led_matrix
from time import sleep

l = led_matrix.LEDMatrix(1,1)
for x in range(0,8):
	for y in range(0,8):
		l.point(x,y)
		l.show()
#		sleep(1)
