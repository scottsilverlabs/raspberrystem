#Import accel module
from rstem import accel
import RPi.GPIO as GPIO

#Initialize GPIO
GPIO.setmode(GPIO.BCM)

#Initialize accel
accel.init(1)

#Enable motion detection on interrupt pin 2
accel.enable_freefall_motion(1, 2)

#Set the debounce counter to 0
accel.freefall_motion_debounce(0)

#Set the debounce mode to default and the threshold to 1.1
accel.freefall_motion_threshold(1, 1.1)

#Make the function that will run when motion is detected
def on_motion(channel):
	print("Motion!")

#Setup sensor pin
GPIO.setup(4, GPIO.IN)

#Bind function to GPIO pin attached to INT2
GPIO.add_event_detect(4, GPIO.RISING, callback=on_motion)

#Run until user kills process
try:
	while True:
		pass
except KeyboardInterrupt:
	GPIO.cleanup()