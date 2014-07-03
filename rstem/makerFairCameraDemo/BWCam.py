#!/usr/bin/env python
import io
import numpy as np
import cv2
import time
cap = cv2.VideoCapture(-1)
cap.set(3, 64) #width
cap.set(4, 64) #height

while True:
	
	ret, img = cap.read()
	grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	thresh = cv2.adaptiveThreshold(grey, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 2)
	thresh = cv2.resize(thresh, None, fx=8, fy=8, interpolation = cv2.INTER_NEAREST)
	cv2.imshow("thresh", thresh)
	k = cv2.waitKey(5) & 0xFF
	if k == 27:
		break

cap.release()
cv2.destroyAllWindows()
