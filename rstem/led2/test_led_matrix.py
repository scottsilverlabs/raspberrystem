#!/usr/bin/env python
from rstem import led2
from time import sleep

led2.initMatrices([(0,0,90),(0,0,90)])
for x in range(0,8):
	for y in range(0,8):
		led2.point(x,y)
		led2.show()
#		sleep(1)
