#!/usr/bin/env python
import io
import numpy as np
import cv2

cap = cv2.VideoCapture(0)
cap.set(3, 64) #width
cap.set(4, 64) #height
cv2.namedWindow("thresh")
cv2.namedWindow("grey")
cv2.namedWindow("edge")
cv2.cv.MoveWindow("grey", 512, 0)
cv2.cv.MoveWindow("edge", 1024, 0)
while True:
	
	ret, img = cap.read()
	grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	canny = cv2.Canny(grey, 100, 200)
	np.multiply(np.round(np.divide(grey, 4)), 4)
	thresh = cv2.adaptiveThreshold(grey, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 3, 2)
	thresh = cv2.resize(thresh, None, fx=8, fy=8, interpolation = cv2.INTER_NEAREST)
	grey = cv2.resize(grey, None, fx = 8, fy = 8, interpolation = cv2.INTER_NEAREST)
        canny = cv2.resize(canny, None, fx = 8, fy = 8, interpolation = cv2.INTER_NEAREST)
	cv2.imshow("thresh", thresh)
	cv2.imshow("grey", grey)
	cv2.imshow("edge", canny)
	k = cv2.waitKey(5) & 0xFF
	if k == 27:
		break

cap.release()
cv2.destroyAllWindows()
