'''
HW test of LED Matrix.  

3 matrices in chain, UUT in the middle, connected vertically (i.e. clockwise
rotated 90 degrees).  MISO should be hooked up.  
'''
import testing_log
import importlib
import testing
from rstem.led_matrix import FrameBuffer, Text, Sprite
import time

VERTICAL_THREE_MATRIX_LAYOUT = [(0,16,90),(0,8,90),(0,0,90)]

@testing.manual_output
def line():
    '''A line from the lower left to the upper right.
    '''
    
    fb = FrameBuffer(matrix_layout=VERTICAL_THREE_MATRIX_LAYOUT)
    fb.erase()
    fb.line((0,0),(fb.width,fb.height))
    fb.show()

@testing.manual_output
def vertical_bars():
    '''A vertical bar on all LED Matrices moving from far left to far right
    in about 1 second.
    '''
    
    fb = FrameBuffer(matrix_layout=VERTICAL_THREE_MATRIX_LAYOUT)
    for x in range(8):
        fb.erase()
        fb.line((x,0),(x,fb.height))
        fb.show()
        time.sleep(0.1)

@testing.manual_output
def horizontal_bars():
    '''A horizontal bar on the LED Matrix UUT moving from bottom to top in about 1
    second.
    '''
    fb = FrameBuffer(matrix_layout=VERTICAL_THREE_MATRIX_LAYOUT)
    for y in range(8,16):
        fb.erase()
        fb.line((0,y),(fb.width,y))
        fb.show()
        time.sleep(0.1)

@testing.manual_output
def one_two_three():
    '''One, two, and three should be displayed on the three matrices, from top
    to bottom.
    '''
    numbers = [Text('3'), Text('2'), Text('1')]
    fb = FrameBuffer(matrix_layout=VERTICAL_THREE_MATRIX_LAYOUT)
    fb.erase()
    for i in range(3):
        fb.draw(numbers[i], (2,i*8))
    fb.show()
    return True

@testing.manual_output
def brightness():
    '''All matrices show displays all LEDs lit, from min to max brightness over about 1 second.
    Should be left at max brightness.
    '''
    fb = FrameBuffer(matrix_layout=VERTICAL_THREE_MATRIX_LAYOUT)
    for i in range(16):
        fb.erase(i)
        fb.show()
        time.sleep(0.07)
    return True

@testing.automatic
def verify_detect():
    num = FrameBuffer.detect()
    return num == 3


