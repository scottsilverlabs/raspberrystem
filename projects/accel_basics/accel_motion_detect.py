#Attach resistor and led between INT2 on the accelerometer and GND
#Import accel module
from rstem import accel

#Initialize accel
accel.init(1)

#Enable motion detection on interrupt pin 2
accel.enable_freefall_motion(1, 2)

#Set the debounce counter to 0
accel.freefall_motion_debounce(0)

#Set the debounce mode to default and the threshold to 1.1
accel.freefall_motion_threshold(1, 1.1)

#Now tap the surface the case in on and the accelerometer will detect it