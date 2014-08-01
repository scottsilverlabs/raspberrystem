#!/usr/bin/env python
import numpy as np
import cv2
import time
from rstem import led_matrix
GRID_SIZE = 2
cap = cv2.VideoCapture(-1)
cap.set(3, 8*GRID_SIZE) #width
cap.set(4, 8*GRID_SIZE) #height
cap.set
led_matrix.init_grid(GRID_SIZE)

try:
	while True:
		led_matrix.fill(0)
		ret, img = cap.read()
		img = cv2.flip(img, 0)
		grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		thresh = cv2.adaptiveThreshold(grey, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 1)
		led_matrix.frame(thresh)
		led_matrix.show()
except KeyboardInterrupt:
	pass	
finally:
	cap.release()
	led_matrix.cleanup()
