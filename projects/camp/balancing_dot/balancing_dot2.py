from rstem.led_matrix import FrameBuffer
import time

fb = FrameBuffer()

x, y = (3, 3)
while True:
    fb.erase()
    fb.point(x, y)
    fb.show()
    
    time.sleep(.1)


