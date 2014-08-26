#!/usr/bin/env python
import numpy as np
import cv2
import time
from rstem import led_matrix
ANGLE_FACTOR = 2
GRID_SIZE = 6
IMAGE_SIZE = ANGLE_FACTOR*8*GRID_SIZE
cap = cv2.VideoCapture(-1)
cap.set(3, IMAGE_SIZE) #width
cap.set(4, IMAGE_SIZE) #height
cap.set(11, 1)
led_matrix.init_grid(GRID_SIZE, GRID_SIZE)
offset = int(round( (IMAGE_SIZE-(8*GRID_SIZE))/2 ))
try:
	while True:
		led_matrix.fill(0)
		ret, img = cap.read()
		img = cv2.flip(img, 0)
		new_img = img[offset:offset+8*GRID_SIZE,offset:offset+8*GRID_SIZE]
		grey = cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)
		thresh = cv2.adaptiveThreshold(grey, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 3)
		led_matrix.frame(thresh)
		led_matrix.show()
except KeyboardInterrupt:
	pass	
finally:
	cap.release()
	led_matrix.cleanup()
