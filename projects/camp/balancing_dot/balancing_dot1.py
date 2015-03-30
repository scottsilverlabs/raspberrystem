from rstem.led_matrix import FrameBuffer

fb = FrameBuffer()

x, y = (3, 3)
fb.erase()
fb.point(x, y)
fb.show()
    
