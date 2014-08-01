#!/usr/bin/env python
import numpy as np
import cv2
from rstem import led_matrix
GRID_SIZE = 2
cap = cv2.VideoCapture(0)
cap.set(3, 8*GRID_SIZE) #width
cap.set(4, 8*GRID_SIZE) #height
led_matrix.init_grid(GRID_SIZE)
try:
	while True:
		led_matrix.fill(0)
		ret, img = cap.read()
		img = cv2.flip(img, 0)
		grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		grey = np.round(np.divide(grey, 16))
		led_matrix.frame(grey)
		led_matrix.show()
except KeyboardInterrupt:
	pass
finally:
	cap.release()

