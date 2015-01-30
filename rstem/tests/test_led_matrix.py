import testing
import time
from functools import partial
from rstem.led_matrix import FrameBuffer

'''
Automatic API tests for LED Matrix.
'''

'''
- displays tests
- drawing tests
- speed tests
    - functions -> FrameBuffer class
        - Remove
            def frame()
            def sprite(sprite, origin=(0, 0), crop_origin=(0, 0), crop_dimensions=None)
            def text(text, origin=(0, 0), crop_origin=(0, 0), 
                crop_dimensions=None, font_name='small', font_path=None)
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
                - old:
                    def init_grid(num_rows=1, num_cols=None, angle=0, spi_port=0)
                    def init_matrices(mat_list=[(0, 0, 0)], spi_port=0)
                        - removed math_coords
                        - removed spi_speed
                        - return the number of matrices
            def draw(sprite, origin)
            def show()
            def detect()
        - Add
            - test reliability of SPI chain
- Classes
    - class LEDSprite rename Sprite
        - Remove
            def flipped_horizontal(self)
            def flipped_vertical(self)
            def inverted(self)
            def rotated(self, angle=90)
            def save_to_file(self, filename)
            def copy(self)
        - Keep
            def __init__(self, filename=None, height=0, width=0, color=0)
            def __add__(self, sprite)
            def add(self, sprite, offset, corner)
            def flip_horizontal(self)
            def flip_vertical(self)
            def invert(self)
            def rotate(self, angle=90)
            def get_pixel(self, x, y)
            def set_pixel(self, point, color=15)
                set via get/setitem?
        - Add
            def crop(origin=(0, 0), dimensions=None)
    - LEDText rename Text
        def __init__(self, message, char_spacing=1, font_name='small', font_path=None)
        All inherited function from Sprite
'''

def makefb(lines):
    rows = []
    for line in lines.splitlines():
        if not line.strip():
            continue
        cols = [int(col, 16) for col in line.strip()]
        rows += [cols]
    fb_transposed = list(reversed(rows))
    fb = [list(z) for z in zip(*fb_transposed)]
    return fb


def erased_fb():
    return makefb('00000000\n' * 8)
    
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
# Timing functions
#

def timeit(f, loops=10000):
    start = time.time()
    for i in range(loops):
        f()
    period = (time.time() - start) / loops
    freq = 1.0 / period
    print("Time per call: {:.2f} usecs".format(period * 1000000))
    print("Freq : {:.0f} Hz".format(freq))
    return freq
    
@testing.automatic
def time_point():
    fb = FrameBuffer(matrix_list=[(0,0)])
    return timeit(partial(fb.point, 0, 0)) > 40000

@testing.automatic
def time_show():
    fb = FrameBuffer(matrix_list=[(0,0)])
    fb.rect((0,0),(4,5), color=1)
    fb.rect((2,2),(6,6), color=2)
    fb.rect((5,1),(3,3), color=3)
    fb.rect((1,5),(4,2), color=4)
    fb.show()
    #return timeit(partial(fb.show), loops=200) > 300

