from rstem.led_matrix import FrameBuffer, Sprite
import time

arrow0deg = Sprite("""
    --------
    --------
    -----F--
    ------F-
    FFFFFFFF
    ------F-
    -----F--
    --------
    """)
arrow15deg = Sprite("""
    --------
    -----F--
    ------F-
    ----FFFF
    FFFF--F-
    -----F--
    --------
    --------
    """)
arrow30deg = Sprite("""
    --------
    ----FFFF
    ------FF
    ----FF-F
    ---F---F
    -FF-----
    F-------
    --------
    """)
arrow45deg = Sprite("""
    ----FFFF
    ------FF
    -----F-F
    ----F--F
    ---F----
    --F-----
    -F------
    F-------
    """)

arrow60deg = Sprite(arrow30deg).flip().rotate(-90)
arrow75deg = Sprite(arrow15deg).flip().rotate(-90)
arrows = [
    Sprite(arrow0deg).rotate(0),
    Sprite(arrow15deg).rotate(0),
    Sprite(arrow30deg).rotate(0),
    Sprite(arrow45deg).rotate(0),
    Sprite(arrow60deg).rotate(0),
    Sprite(arrow75deg).rotate(0),
    Sprite(arrow0deg).rotate(90),
    Sprite(arrow15deg).rotate(90),
    Sprite(arrow30deg).rotate(90),
    Sprite(arrow45deg).rotate(90),
    Sprite(arrow60deg).rotate(90),
    Sprite(arrow75deg).rotate(90),
    Sprite(arrow0deg).rotate(180),
    Sprite(arrow15deg).rotate(180),
    Sprite(arrow30deg).rotate(180),
    Sprite(arrow45deg).rotate(180),
    Sprite(arrow60deg).rotate(180),
    Sprite(arrow75deg).rotate(180),
    Sprite(arrow0deg).rotate(270),
    Sprite(arrow15deg).rotate(270),
    Sprite(arrow30deg).rotate(270),
    Sprite(arrow45deg).rotate(270),
    Sprite(arrow60deg).rotate(270),
    Sprite(arrow75deg).rotate(270),
    ]

fb = FrameBuffer()
while True:
    for arrow in arrows:
        fb.erase()
        fb.draw(arrow)
        fb.show()
        time.sleep(0.1)
