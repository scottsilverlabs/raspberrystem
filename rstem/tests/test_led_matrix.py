import testing
import time
from functools import partial
from rstem.led_matrix import FrameBuffer, Sprite, Text
import copy

'''
Automatic API tests for LED Matrix.
'''

'''
- functions -> FrameBuffer class
    - Keep
        __init__(merge of init_grid and init_matrices)
            - new:
                def __init__(num_rows=None, matrix_list=None, spi_port=0)
                    - num_rows=None favor minimal
                      rectangle, landscape before
                      portrait
                    - matrix_list:
                        list of either:
                            - relative corridinates (i.e. (-8,0))
                            - int angle
    - Add
        - test reliability of SPI chain
- Sprite
    - TBD
        def get_pixel(self, x, y)
        def set_pixel(self, point, color=15)
    - Add
        def crop(origin=(0, 0), dimensions=None)
'''

def makefb(lines):
    # Remove whitespace from lines
    lines = (line.replace(' ', '') for line in lines.splitlines())
    # remove blank lines
    lines = (line for line in lines if line)
    reversed_transposed_fb = \
        [[int(color, 16) if color != '-'  else -1 for color in line] for line in lines]
    transposed_fb = list(reversed(reversed_transposed_fb))
    fb = [list(z) for z in zip(*transposed_fb)]
    return fb


def erased_fb():
    return makefb('00000000\n' * 8)
    
def timeit(f, loops=10000):
    start = time.time()
    for i in range(loops):
        f()
    period = (time.time() - start) / loops
    freq = 1.0 / period
    print("Time per call: {:.2f} usecs".format(period * 1000000))
    print("Freq : {:.2f} Hz".format(freq))
    return freq
    
#########################################################################
# __init__() tests
#

@testing.automatic
def default_erased():
    fb = FrameBuffer(matrix_list=[(0,0)])
    return fb._framebuffer() == erased_fb()

#########################################################################
# erase() tests
#

@testing.automatic
def erase1():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.erase(0xf)
    fb.erase()
    return fb._framebuffer() == makefb('00000000\n' * 8)

@testing.automatic
def erase2():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.erase(3)
    return fb._framebuffer() == makefb('33333333\n' * 8)

@testing.automatic
def erase3():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.erase(7)
    return fb._framebuffer() == makefb('77777777\n' * 8)

#########################################################################
# point() tests
#

@testing.automatic
def point1():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point(0,0)
    expected_fb = makefb('''
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        F0000000
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def point2():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point((0,0), color=1)
    expected_fb = makefb('''
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        10000000
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def point3():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point(1,2,color=3)
    expected_fb = makefb('''
        00000000
        00000000
        00000000
        00000000
        00000000
        03000000
        00000000
        00000000
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def point4():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point(7,7,color=10)
    expected_fb = makefb('''
        0000000A
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def point5():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point(7,7,color=10)
    expected_fb = makefb('''
        0000000A
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        ''')
    return fb._framebuffer() == expected_fb

    fb.point(0,0,1)
    fb.point(0,7,2)
    fb.point(7,0,3)
    fb.point(7,7,4)
@testing.automatic
def out_of_bounds_point1():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point(-1, 0)
    return fb._framebuffer() == erased_fb()

@testing.automatic
def out_of_bounds_point2():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point(0, -1)
    return fb._framebuffer() == erased_fb()

@testing.automatic
def out_of_bounds_point3():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point(fb.width, 0)
    return fb._framebuffer() == erased_fb()

@testing.automatic
def out_of_bounds_point4():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.point(0, fb.height)
    return fb._framebuffer() == erased_fb()

@testing.automatic
def time_point():
    fb = FrameBuffer(matrix_list=[(0,0)])
    return timeit(partial(fb.point, 0, 0)) > 40000

#########################################################################
# line() tests
#

@testing.automatic
def line1():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.line((0,7),(7,7))
    expected_fb = makefb('''
        ffffffff
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def line2():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.line((0,0),(0,7))
    expected_fb = makefb('''
        f0000000
        f0000000
        f0000000
        f0000000
        f0000000
        f0000000
        f0000000
        f0000000
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def line3():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.line((0,0),(7,7))
    expected_fb = makefb('''
        0000000f
        000000f0
        00000f00
        0000f000
        000f0000
        00f00000
        0f000000
        f0000000
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def line4():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.line((0,0),(7,7))
    fb.line((7,0),(0,7), color=1)
    fb.line((2,0),(2,7), color=2)
    fb.line((0,2),(7,2), color=3)
    expected_fb = makefb('''
        1020000f
        012000f0
        00200f00
        0021f000
        002f1000
        33333333
        0f200010
        f0200001
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def line5():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.line((1,3),(6,5))
    expected_fb = makefb('''
        00000000
        00000000
        00000ff0
        000ff000
        0ff00000
        00000000
        00000000
        00000000
        ''')
    return fb._framebuffer() == expected_fb


#########################################################################
# rect() tests
#

@testing.automatic
def rect1():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.rect((0,0),(8,8))
    expected_fb = makefb('''
        ffffffff
        f000000f
        f000000f
        f000000f
        f000000f
        f000000f
        f000000f
        ffffffff
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def rect2():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.rect((0,0),(8,8), fill=True)
    expected_fb = makefb('''
        ffffffff
        ffffffff
        ffffffff
        ffffffff
        ffffffff
        ffffffff
        ffffffff
        ffffffff
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def rect3():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.rect((2,1),(3,5), fill=True)
    expected_fb = makefb('''
        00000000
        00000000
        00fff000
        00fff000
        00fff000
        00fff000
        00fff000
        00000000
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def rect4():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.rect((0,0),(4,5), color=1)
    fb.rect((2,2),(6,6), color=2)
    fb.rect((5,1),(3,3), color=3)
    fb.rect((1,5),(4,2), color=4)
    expected_fb = makefb('''
        00222222
        04444002
        04444002
        11210002
        10210333
        10222323
        10010333
        11110000
        ''')
    return fb._framebuffer() == expected_fb

#########################################################################
# misc tests
#

@testing.automatic
def detect_fail():
    # An unconnected chain should report IOError
    try:
        FrameBuffer.detect()
    except IOError:
        return True
    return False

@testing.automatic
def time_show():
    fb = FrameBuffer(matrix_list=[(0,0)])
    return timeit(partial(fb.show), loops=200) > 300

#########################################################################
# Sprite tests
#

default_sprite = Sprite('''
    1 2 3
    4 5 6
    7 8 9
    a b c
    ''')

@testing.automatic
def sprite_init():
    s = copy.deepcopy(default_sprite)
    expected_bitmap = makefb('''
        123
        456
        789
        abc
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_init_lines_long():
    s = Sprite('''
        1 2 3 4
        4 5 6 a b c
        7 8 9
        a b c d e
        ''')
    expected_bitmap = makefb('''
        123
        456
        789
        abc
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_init_variable_whitespace():
    s = Sprite('''
        1  	2 3    4
        4 				5       6 a b c
        7  8  		  9
        a   b  c d e
        ''')
    expected_bitmap = makefb('''
        123
        456
        789
        abc
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_rotate_90():
    s = copy.deepcopy(default_sprite)
    s.rotate(90)
    expected_bitmap = makefb('''
        369c
        258b
        147a
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_rotate_180():
    s = copy.deepcopy(default_sprite)
    s.rotate(180)
    expected_bitmap = makefb('''
        cba
        987
        654
        321
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_rotate_270():
    s = copy.deepcopy(default_sprite)
    s.rotate(270)
    expected_bitmap = makefb('''
        a741
        b852
        c963
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_rotate_neg_90():
    s = copy.deepcopy(default_sprite)
    s.rotate(-90)
    expected_bitmap = makefb('''
        a741
        b852
        c963
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_rotate_360():
    s = copy.deepcopy(default_sprite)
    s.rotate(360)
    expected_bitmap = makefb('''
        123
        456
        789
        abc
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_flip():
    s = copy.deepcopy(default_sprite)
    s.flip()
    expected_bitmap = makefb('''
        321
        654
        987
        cba
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_flip_vertical():
    s = copy.deepcopy(default_sprite)
    s.rotate(180).flip()
    expected_bitmap = makefb('''
        abc
        789
        456
        123
        ''')
    return expected_bitmap == s._bitmap()

@testing.automatic
def sprite_rotate_bad_angle():
    s = copy.deepcopy(default_sprite)
    try:
        s.rotate(123)
    except ValueError:
        return True
    return False

@testing.automatic
def sprite_time_bitmap():
    s = copy.deepcopy(default_sprite)
    s.rotate(270).flip()
    return timeit(partial(s._bitmap), loops=200) > 300

@testing.automatic
def sprite_draw_default_origin():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.erase(0xE)
    s = copy.deepcopy(default_sprite)
    fb.draw(s)
    expected_fb = makefb('''
        eeeeeeee
        eeeeeeee
        eeeeeeee
        eeeeeeee
        123eeeee
        456eeeee
        789eeeee
        abceeeee
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def sprite_draw():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.erase(0xE)
    s = copy.deepcopy(default_sprite)
    fb.draw(s, origin=(2,3))
    expected_fb = makefb('''
        eeeeeeee
        ee123eee
        ee456eee
        ee789eee
        eeabceee
        eeeeeeee
        eeeeeeee
        eeeeeeee
        ''')
    return fb._framebuffer() == expected_fb

@testing.automatic
def sprite_add():
    one = Sprite('''
        12
        45
        67
        ''')
    two = Sprite('''
        a
        b
        c
        ''')
    new = one + two
    expected_bitmap = makefb('''
        12a
        45b
        67c
        ''')
    return expected_bitmap == new._bitmap()

@testing.automatic
def sprite_add_inconsistent_heights():
    one = Sprite('''
        12
        45
        67
        ''')
    two = Sprite('''
        b
        c
        ''')
    try:
        new = one + two
    except ValueError:
        return True
    return False

@testing.automatic
def sprite_time_large_bitmap_draw_and_show():
    # This is currently quite slow, as it is all done in Python via a 2D array.
    # Speed not needed right now, but may in future move to numpy or CPython
    fb = FrameBuffer(matrix_list=[(0,0)])
    s = Sprite((('5'*16) + '\n')*16)
    def draw():
        fb.draw(s)
        fb.show()
    return timeit(partial(draw), loops=100) > 50

#########################################################################
# Text tests
#

@testing.automatic
def text():
    t = Text("ABCabc")
    expected_bitmap = makefb('''
        --f---ffff---fff--------f----------
        -f-f--f---f-f---f-------f----------
        f---f-f---f-f------fff--ffff---ffff
        f---f-ffff--f---------f-f---f-f----
        fffff-f---f-f------ffff-f---f-f----
        f---f-f---f-f---f-f---f-f---f-f----
        f---f-ffff---fff---ffff-ffff---ffff
        ''')
    return expected_bitmap == t._bitmap()

@testing.automatic
def time_text():
    return timeit(partial(Text, '0123456789'), loops=10) > 5

