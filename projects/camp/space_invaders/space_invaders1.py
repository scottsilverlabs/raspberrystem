from rstem.led_matrix import FrameBuffer

fb = FrameBuffer()

fb.erase()
fb.point(3, 0)
fb.show()
