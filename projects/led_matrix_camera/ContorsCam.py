#!/usr/bin/env python
import numpy as np
import cv2
from rstem import led_matrix
ANGLE_FACTOR = 1
GRID_SIZE = 6
IMAGE_SIZE = ANGLE_FACTOR*8*GRID_SIZE
cap = cv2.VideoCapture(0)
cap.set(3, IMAGE_SIZE) #width
cap.set(4, IMAGE_SIZE) #height
cap.set(11, 1)
led_matrix.init_grid(GRID_SIZE, GRID_SIZE)
offset = int(round( (IMAGE_SIZE-(8*GRID_SIZE))/2 ))
try:
	while True:
		ret, img = cap.read()
		img = cv2.flip(img, 0)
		new_img = img[offset:offset+8*GRID_SIZE,offset:offset+8*GRID_SIZE]
		grey = cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)
		canny = cv2.Canny(grey, 100, 200)
		led_matrix.frame(canny)
		led_matrix.show()
except KeyboardInterrupt:	
	pass
finally:
	led_matrix.cleanup()
	cap.release()

