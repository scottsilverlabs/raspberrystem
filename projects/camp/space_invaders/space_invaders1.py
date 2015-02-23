from rstem.led_matrix import FrameBuffer

fb = FrameBuffer()

fb.erase()
fb.point(3, 0)
fb.point(13, 4)
fb.line((0,0), (20,10))
fb.show()
