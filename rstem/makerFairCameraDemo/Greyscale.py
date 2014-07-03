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
	np.multiply(np.round(np.divide(grey, 4)), 4)
	grey = cv2.resize(grey, None, fx = 8, fy = 8, interpolation = cv2.INTER_NEAREST)
	cv2.imshow("grey", grey)
	k = cv2.waitKey(5) & 0xFF
	if k == 27:
		break

cap.release()
cv2.destroyAllWindows()
