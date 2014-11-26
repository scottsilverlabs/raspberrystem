import RPi.GPIO as gpio
gpio.setmode(gpio.BCM)

pin = 14
gpio.setup(pin, gpio.OUT)
gpio.output(pin, True)
