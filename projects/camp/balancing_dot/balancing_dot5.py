from rstem.accel import Accel
from rstem.led_matrix import FrameBuffer
import time

fb = FrameBuffer()
accel = Accel()

x, y = (3, 3)
while True:
    x_force, y_force, z_force = accel.forces()
    
    x -= min(2, int(x_angle/4.0))
    x = max(0, min(7, x))
    y += min(2, int(y_angle/4.0))
    y = max(0, min(7, y))
    
    fb.erase()
    fb.point(x, y)
    fb.show()
    
    time.sleep(.1)


