from rstem.led_matrix import FrameBuffer

fb = FrameBuffer()

spaceship_position = fb.width / 2

while True:
    fb.erase()

    # Draw spaceship
    fb.point(round(spaceship_position), 0)

    # Show FrameBuffer on LED Matrix
    fb.show()
    time.sleep(0.001)
