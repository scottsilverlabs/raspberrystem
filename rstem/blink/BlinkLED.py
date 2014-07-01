#Basic imports
import RPi.GPIO as GPIO
import time

#Declare pins and setup
led = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(led, GPIO.OUT)

#Blink 10 times
for x in range(0,10):
	GPIO.output(led, True)
	time.sleep(1)
	GPIO.output(led, False)
	time.sleep(1)

#cleanup
GPIO.cleanup()
