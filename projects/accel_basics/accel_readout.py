#Import accel module
from rstem import accel
from time import sleep

#Initialze accelerometer on i2c bus 1, on early Pi's this may be 0 instead
accel.init(1)

#Loop to display values
while True:
    force = accel.read() #Returns a tuple of the form (x, y, z) acceleration
    angles = accel.angles() #Returns a tuple of the form (roll, pitch, elevation) force
#   Print values in a nicely formatted way
    print("X: {0[0]: < 8.4f}    Y: {0[1]: < 8.4f}    Z: {0[2]: < 8.4f}    Roll: {1[0]: < 8.4f}    Pitch: {1[1]: < 8.4f}    Elevation: {1[2]: < 8.4f}".format(force, angles))
    sleep(0.25)