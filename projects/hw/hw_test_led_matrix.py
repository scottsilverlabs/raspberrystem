from rstem.led_matrix import FrameBuffer, Text
import traceback
import sys
import time

def failed(s):
    print(traceback.format_exc())
    print("ERROR: ", s)
    print("TEST FAILED")
    sys.exit()

try:
    fb = FrameBuffer([(0,0,-90),(8,0,-90),(8,8,-90)])
except:
    failed("FrameBuffer() could not be intialized")

if len(fb.matrix_layout) != 3:
    failed("Should be exactly 3 LED Matrices attached")


print("""
Verify that the following sequence occurs:
    - A, B, C is printed on the LEDs (1 second)
    - All LEDs on (1 second)
    - LEDs go from dim to bright (2 seconds)
    - All LEDs go dark.
    - UUT (B) shows horizontal bar go from bottom to top (1 second)
    - UUT shows vertical bar go from left to right (1 second)
    - UUT shows 1 quarter lit (upper left/right, then lower left/right) (1
      second)
    - UUT shows checkerboard with bottom left lit, then inverted checkerboard
      (1.5 seconds)
Any missing LEDs lit is a failure.

Sequence repeats forever - hit CTRL-C to stop.
""")

input("Press Enter to start the test...")

print("TEST SEQUENCE RUNNING - CTRL-C TO END")

while True:
    fb.erase()
    fb.draw(Text("A"), (0,0))
    fb.draw(Text("B"), (8,0))
    fb.draw(Text("C"), (8,8))
    fb.show()
    time.sleep(1)

    fb.erase(0xF)
    fb.show()
    time.sleep(1)

    for color in range(16):
        fb.erase(color)
        fb.show()
        time.sleep(2/16)

    fb.erase()
    fb.show()
    time.sleep(0.2)

    for y in range(8):
        fb.erase()
        fb.line((8,y),(15,y))
        fb.show()
        time.sleep(1/8)

    fb.erase()
    fb.show()
    time.sleep(0.2)

    for x in range(8):
        fb.erase()
        fb.line((8+x,0),(8+x,7))
        fb.show()
        time.sleep(1/8)

    fb.erase()
    fb.show()
    time.sleep(0.2)

    def square(startx, starty):
        fb.erase()
        for i in range(4):
            fb.line((startx,starty+i),(startx+3,starty+i))
        fb.show()
        time.sleep(0.25)

    square(8,4)
    square(12,4)
    square(8,0)
    square(12,0)

    fb.erase()
    for x in range(9,16,2):
        fb.line((x,7),(x+7,0))
    for y in range(0,8,2):
        fb.line((8,y),(15,y-7))
    fb.show()
    time.sleep(0.75)

    fb.erase()
    for x in range(8,16,2):
        fb.line((x,7),(x+7,0))
    for y in range(1,8,2):
        fb.line((8,y),(15,y-7))
    fb.show()
    time.sleep(0.75)
