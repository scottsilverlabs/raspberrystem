from rstem.accel import Accel
from rstem.led_matrix import FrameBuffer
import time

fb = FrameBuffer()
accel = Accel()

TILT_FORCE = 0.1
STEP = 0.1
x, y = (3, 3)
while True:
    x_force, y_force, z_force = accel.forces()
    
    if x_force > TILT_FORCE:
        x -= STEP
    elif x_force < -TILT_FORCE:
        x += STEP

    fb.erase()
    fb.point(round(x), round(y))
    fb.show()
    
    time.sleep(.1)


