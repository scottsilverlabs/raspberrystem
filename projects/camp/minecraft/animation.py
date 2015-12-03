from rstem.led_matrix import FrameBuffer, Sprite
from itertools import cycle
import time

fb = FrameBuffer()

animation = [
    Sprite("""
        00000000
        0000FF00
        000FF000
        000FFF00
        00FFFF00
        000FFF00
        0FF00F00
        0F0000FF
        """),
    Sprite("""
        00000000
        0000FF00
        0000F000
        00FFFF00
        0F0FF0F0
        000FFF00
        0FF00F00
        00000FF0
        """),
    Sprite("""
        00000000
        0000FF00
        000FF000
        000FF000
        000FF000
        000FF000
        00FFF000
        000FF000
        """),
    Sprite("""
        0000FF00
        000FF000
        000FFF00
        00FFFF00
        000FFF00
        00F00F00
        00F0F000
        00F00000
        """),
    ]

animation = cycle(animation)
while True:
    sprite = next(animation)

    fb.erase()
    fb.draw(sprite)
    fb.show()

    time.sleep(0.1)

