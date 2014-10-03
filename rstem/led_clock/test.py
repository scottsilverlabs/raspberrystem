#!/usr/bin/env python
import led_clock
from time import sleep

led_clock.init_SPI(100000, 0)

for i in range(0,10):
	for j in range(0,10):
		for k in range(0,10):
			for l in range(0,10):
				led_clock.digit(1, i, 0)
				led_clock.digit(2, j, 0)
				led_clock.digit(3, k, 0)
				led_clock.digit(4, l, 0)
				led_clock.flush()
				sleep(1.0/10.0)
