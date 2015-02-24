'''
HW test of LED Matrix.  

Any number of matrices can be in chain.  Expects that they are connected
vertically (i.e. clockwise rotated 90 degrees).  MISO should be hooked up.  
'''
import testing_log
import testing
from rstem.led_matrix import FrameBuffer, Text
import time

@testing.manual_output
def char_on_each_matrix():
    '''Verify that the numbers 0-9, A-Z are in the vertical chain of LEDs,
    lowest number at the bottom.
    '''
    chars = [Text(chr(ord('0')+i)) for i in range(10)]
    chars += [Text(chr(ord('A')+i)) for i in range(26)]

    num = FrameBuffer.detect()
    matrix_layout = [(0,y*8,90) for y in reversed(range(num))]
    fb = FrameBuffer(matrix_layout=matrix_layout)

    fb.erase()
    for i in range(num):
        fb.draw(chars[i], (2,8*i))
    fb.show()

