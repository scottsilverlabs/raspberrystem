#!/usr/bin/env python
import picamera
import io
import numpy as np
import cv2

camera = picamera.PiCamera()
camera.vflip = True
camera.resolution = (64, 64)
t = 0
while t < 5:
	stream = io.BytesIO()
	camera.capture(stream, format='jpeg')
	data = np.fromstring(stream.getvalue(), dtype=np.uint8)
	img = cv2.imdecode(data, 0)
	grey = cv2.imdecode(data, 0)
	np.round(np.multiply(np.divide(grey, 4), 4))
	sum = 0.0
	for x in range (0,64):
		for y in range(0,64):
			sum = sum + img[x][y]
	sum = sum/(64*64)
#	ret, thresh = cv2.threshold(img, sum, 255, cv2.THRESH_BINARY)
#	thresh = cv2.resize(thresh, None, fx=5, fy=5, interpolation = cv2.INTER_LINEAR)
	grey = cv2.resize(grey, None, fx = 5, fy = 5, interpolation = cv2.INTER_LINEAR)
#	cv2.imshow("thresh", thresh)
	print(img)
	cv2.imshow("grey", grey)
	k = cv2.waitKey(5) & 0xFF
	if k == 27:
		break
	t = t + 1

cv2.destroyAllWindows()
