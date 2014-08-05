#!/usr/bin/env python
import numpy as np
import cv2
from rstem import led_matrix
GRID_SIZE = 2
cap = cv2.VideoCapture(0)
cap.set(3, 8*GRID_SIZE) #width
cap.set(4, 8*GRID_SIZE) #height
cap.set(11, 1)
led_matrix.init_grid(GRID_SIZE)
try:
	while True:
		ret, img = cap.read()
		img = cv2.flip(img, 0)
		grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		canny = cv2.Canny(grey, 100, 200)
		led_matrix.frame(canny)
		led_matrix.show()
except KeyboardInterrupt:	
	pass
finally:
	led_matrix.cleanup()
	cap.release()

