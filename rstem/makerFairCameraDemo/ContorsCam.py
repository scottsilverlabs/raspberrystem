#!/usr/bin/env python
import io
import numpy as np
import cv2

cap = cv2.VideoCapture(0)
cap.set(3, 64) #width
cap.set(4, 64) #height
while True:
	ret, img = cap.read()
	grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	canny = cv2.Canny(grey, 100, 200)
	canny = cv2.resize(canny, None, fx = 8, fy = 8, interpolation = cv2.INTER_NEAREST)
	cv2.imshow("edge", canny)
	k = cv2.waitKey(5) & 0xFF
	if k == 27:
		break

cap.release()
cv2.destroyAllWindows()
