'''
API tests for LED Matrix.

The automatic tests require no LED matrix attached.  The manual tests require a
single matrix rotated clockwise 90 degrees.
'''

'''
- functions -> FrameBuffer class
    - Add
        - test reliability of SPI chain
- Sprite
    - TBD
        def get_pixel(self, x, y)
        def set_pixel(self, point, color=15)

'''
import testing
import time
from functools import partial
from rstem.led_matrix import FrameBuffer, Sprite, Text
import copy

def makefb(lines):
    # Remove whitespace from lines
    lines = (line.replace(' ', '') for line in lines.splitlines())
    # remove blank lines
    lines = (line for line in lines if line)
    reversed_transposed_fb = \
        [[int(color, 16) if color != '-' else -1 for color in line] for line in lines]
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
    
def arrays_equal(expected, actual):
    e = [line.strip().upper() for line in str(expected).splitlines() if line.strip()]
    a = [line.strip().upper() for line in str(actual).splitlines() if line.strip()]
    print("EXPECTED:")
    for line in e:
        print('\t', line)
    print("ACTUAL:")
    for line in a:
        print('\t', line)
    return a == e

#########################################################################
# __init__() tests
#

@testing.automatic
def default_erased():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    return fb._framebuffer() == erased_fb()

@testing.automatic
def init_two():
    fb = FrameBuffer(matrix_layout=[(0,0,0), (8,0,0)])
    fb.line((0,0),(fb.width, fb.height), color=0xa)
    expected_fb = '''
        00000000000000aa
        000000000000aa00
        0000000000aa0000
        00000000aa000000
        000000aa00000000
        0000aa0000000000
        00aa000000000000
        aa00000000000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def init_two_offset():
    fb = FrameBuffer(matrix_layout=[(0,0,0), (8,3,0)])
    fb.line((0,0),(fb.width, fb.height), color=0xa)
    expected_fb = '''
        00000000000000aa
        0000000000000a00
        00000000000aa000
        0000000000a00000
        000000000a000000
        0000000aa0000000
        000000a000000000
        0000aa0000000000
        000a000000000000
        0aa0000000000000
        a000000000000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def init_three_diagonal():
    fb = FrameBuffer(matrix_layout=[(0,0,0), (8,8,0), (16,16,0)])
    expected_fb = (('0' * 24) + '\n') * 24
    return arrays_equal(expected_fb, fb)

@testing.automatic
def init_two_bad_angle():
    try:
        fb = FrameBuffer(matrix_layout=[(0,0,0), (8,0,123)])
    except ValueError:
        return True
    return False

#########################################################################
# erase() tests
#

@testing.automatic
def erase1():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.erase(0xf)
    fb.erase()
    return fb._framebuffer() == makefb('00000000\n' * 8)

@testing.automatic
def erase2():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.erase(3)
    return fb._framebuffer() == makefb('33333333\n' * 8)

@testing.automatic
def erase3():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.erase(7)
    return fb._framebuffer() == makefb('77777777\n' * 8)

#########################################################################
# point() tests
#

@testing.automatic
def point1():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point(0,0)
    expected_fb = '''
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        F0000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def point2():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point((0,0), color=1)
    expected_fb = '''
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        10000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def point3():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point(1,2,color=3)
    expected_fb = '''
        00000000
        00000000
        00000000
        00000000
        00000000
        03000000
        00000000
        00000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def point4():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point(7,7,color=10)
    expected_fb = '''
        0000000A
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def point5():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point(7,7,color=10)
    expected_fb = '''
        0000000A
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        '''
    return arrays_equal(expected_fb, fb)

    fb.point(0,0,1)
    fb.point(0,7,2)
    fb.point(7,0,3)
    fb.point(7,7,4)
@testing.automatic
def out_of_bounds_point1():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point(-1, 0)
    return fb._framebuffer() == erased_fb()

@testing.automatic
def out_of_bounds_point2():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point(0, -1)
    return fb._framebuffer() == erased_fb()

@testing.automatic
def out_of_bounds_point3():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point(fb.width, 0)
    return fb._framebuffer() == erased_fb()

@testing.automatic
def out_of_bounds_point4():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.point(0, fb.height)
    return fb._framebuffer() == erased_fb()

@testing.automatic
def time_point():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    return timeit(partial(fb.point, 0, 0)) > 40000

#########################################################################
# line() tests
#

@testing.automatic
def line1():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.line((0,7),(7,7))
    expected_fb = '''
        FFFFFFFF
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        00000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def line2():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.line((0,0),(0,7))
    expected_fb = '''
        F0000000
        F0000000
        F0000000
        F0000000
        F0000000
        F0000000
        F0000000
        F0000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def line3():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.line((0,0),(7,7))
    expected_fb = '''
        0000000F
        000000F0
        00000F00
        0000F000
        000F0000
        00F00000
        0F000000
        F0000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def line4():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.line((0,0),(7,7))
    fb.line((7,0),(0,7), color=1)
    fb.line((2,0),(2,7), color=2)
    fb.line((0,2),(7,2), color=3)
    expected_fb = '''
        1020000F
        012000F0
        00200F00
        0021F000
        002F1000
        33333333
        0F200010
        F0200001
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def line5():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.line((1,3),(6,5))
    expected_fb = '''
        00000000
        00000000
        00000FF0
        000FF000
        0FF00000
        00000000
        00000000
        00000000
        '''
    return arrays_equal(expected_fb, fb)


#########################################################################
# rect() tests
#

@testing.automatic
def rect1():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.rect((0,0),(8,8))
    expected_fb = '''
        FFFFFFFF
        F000000F
        F000000F
        F000000F
        F000000F
        F000000F
        F000000F
        FFFFFFFF
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def rect2():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.rect((0,0),(8,8), fill=True)
    expected_fb = '''
        FFFFFFFF
        FFFFFFFF
        FFFFFFFF
        FFFFFFFF
        FFFFFFFF
        FFFFFFFF
        FFFFFFFF
        FFFFFFFF
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def rect3():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.rect((2,1),(3,5), fill=True)
    expected_fb = '''
        00000000
        00000000
        00FFF000
        00FFF000
        00FFF000
        00FFF000
        00FFF000
        00000000
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def rect4():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.rect((0,0),(4,5), color=1)
    fb.rect((2,2),(6,6), color=2)
    fb.rect((5,1),(3,3), color=3)
    fb.rect((1,5),(4,2), color=4)
    expected_fb = '''
        00222222
        04444002
        04444002
        11210002
        10210333
        10222323
        10010333
        11110000
        '''
    return arrays_equal(expected_fb, fb)

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
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
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
    expected_bitmap = '''
        123
        456
        789
        abc
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_init_lines_long():
    s = Sprite('''
        1 2 3 4
        4 5 6 a b c
        7 8 9
        a b c d e
        ''')
    expected_bitmap = '''
        123
        456
        789
        abc
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_init_variable_whitespace():
    s = Sprite('''
        1  	2 3    4
        4 				5       6 a b c
        7  8  		  9
        a   b  c d e
        ''')
    expected_bitmap = '''
        123
        456
        789
        abc
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_rotate_90():
    s = copy.deepcopy(default_sprite)
    s.rotate(90)
    expected_bitmap = '''
        369c
        258b
        147a
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_rotate_180():
    s = copy.deepcopy(default_sprite)
    s.rotate(180)
    expected_bitmap = '''
        cba
        987
        654
        321
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_rotate_270():
    s = copy.deepcopy(default_sprite)
    s.rotate(270)
    expected_bitmap = '''
        a741
        b852
        c963
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_rotate_neg_90():
    s = copy.deepcopy(default_sprite)
    s.rotate(-90)
    expected_bitmap = '''
        a741
        b852
        c963
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_rotate_360():
    s = copy.deepcopy(default_sprite)
    s.rotate(360)
    expected_bitmap = '''
        123
        456
        789
        abc
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_flip():
    s = copy.deepcopy(default_sprite)
    s.flip()
    expected_bitmap = '''
        321
        654
        987
        cba
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_flip_vertical():
    s = copy.deepcopy(default_sprite)
    s.rotate(180).flip()
    expected_bitmap = '''
        abc
        789
        456
        123
        '''
    return arrays_equal(expected_bitmap, s)

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
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.erase(0xE)
    s = copy.deepcopy(default_sprite)
    fb.draw(s)
    expected_fb = '''
        EEEEEEEE
        EEEEEEEE
        EEEEEEEE
        EEEEEEEE
        123EEEEE
        456EEEEE
        789EEEEE
        ABCEEEEE
        '''
    return arrays_equal(expected_fb, fb)

@testing.automatic
def sprite_draw():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    fb.erase(0xE)
    s = copy.deepcopy(default_sprite)
    fb.draw(s, origin=(2,3))
    expected_fb = '''
        EEEEEEEE
        EE123EEE
        EE456EEE
        EE789EEE
        EEABCEEE
        EEEEEEEE
        EEEEEEEE
        EEEEEEEE
        '''
    return arrays_equal(expected_fb, fb)

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
    expected_bitmap = '''
        12a
        45b
        67c
        '''
    return arrays_equal(expected_bitmap, new)

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
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    s = Sprite((('5'*16) + '\n')*16)
    def draw():
        fb.draw(s)
        fb.show()
    return timeit(partial(draw), loops=100) > 50

@testing.automatic
def sprite_crop():
    s = copy.deepcopy(default_sprite)
    s.crop((1,2))
    expected_bitmap = '''
        23
        56
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_crop_x_only():
    s = copy.deepcopy(default_sprite)
    s.crop((1,0))
    expected_bitmap = '''
        23
        56
        89
        bc
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_crop_y_only():
    s = copy.deepcopy(default_sprite)
    s.crop((0,1))
    expected_bitmap = '''
        123
        456
        789
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_crop_dimensions():
    s = copy.deepcopy(default_sprite)
    s.crop((1,1),(2,2))
    expected_bitmap = '''
        56
        89
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_crop_and_rotate():
    s = copy.deepcopy(default_sprite)
    s.crop((1,2))
    s.rotate()
    expected_bitmap = '''
        36
        25
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_rotate_and_crop():
    s = copy.deepcopy(default_sprite)
    s.rotate()
    s.crop((1,2))
    expected_bitmap = '''
        69c
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_reset():
    s = copy.deepcopy(default_sprite)
    s.rotate().reset()
    expected_bitmap = '''
        123
        456
        789
        abc
        '''
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_reinit():
    s = copy.deepcopy(default_sprite)
    expected_bitmap = Sprite(s)
    return arrays_equal(expected_bitmap, s)

@testing.automatic
def sprite_reinit_change():
    original = copy.deepcopy(default_sprite)
    modified = Sprite(original)
    modified.bitmap[0][0]=0
    expected_modified = '''
        123
        456
        789
        0bc
        '''
    expected_original = '''
        123
        456
        789
        abc
        '''
    return arrays_equal(expected_original, original) \
            and arrays_equal(expected_modified, modified)

#########################################################################
# Text tests
#

@testing.automatic
def text():
    t = Text("ABCabc")
    expected_bitmap = '''
        --F---FFFF---FFF--------F----------
        -F-F--F---F-F---F-------F----------
        F---F-F---F-F------FFF--FFFF---FFFF
        F---F-FFFF--F---------F-F---F-F----
        FFFFF-F---F-F------FFFF-F---F-F----
        F---F-F---F-F---F-F---F-F---F-F----
        F---F-FFFF---FFF---FFFF-FFFF---FFFF
        '''
    return arrays_equal(expected_bitmap, t)

@testing.automatic
def small_text():
    t = Text("ABCabc", font_name='3x5')
    expected_bitmap = '''
        -F--FF---FF-FF--F------
        F-F-F-F-F-----F-F------
        FFF-FF--F---FFF-FFF-FFF
        F-F-F-F-F---F-F-F-F-F--
        F-F-FF---FF-FFF-FFF-FFF
        '''
    return arrays_equal(expected_bitmap, t)

@testing.automatic
def small_2spaces_text():
    t = Text("ABCabc", char_spacing=2, font_name='3x5')
    expected_bitmap = '''
        -F---FF----FF--FF---F-------
        F-F--F-F--F------F--F-------
        FFF--FF---F----FFF--FFF--FFF
        F-F--F-F--F----F-F--F-F--F--
        F-F--FF----FF--FFF--FFF--FFF
        '''
    return arrays_equal(expected_bitmap, t)

@testing.automatic
def time_text():
    return timeit(partial(Text, '0123456789'), loops=10) > 5

#########################################################################
# Manual tests
#

@testing.manual_output
def brightness():
    '''All matrices show displays all LEDs lit, from min to max brightness over about 1 second.
    Should be left at max brightness.
    '''
    fb = FrameBuffer(matrix_layout=[(0,0,90)])
    for i in range(16):
        fb.erase(i)
        fb.show()
        time.sleep(0.1)

@testing.manual_output
def diagonal_wave_animation():
    '''Displays a diagonal wave animation over ~3 seconds.  Movement should
    appear in the direction from the botton right to the top left.
    '''
    fb = FrameBuffer(matrix_layout=[(0,0,90)])
    colors = list(range(16)) + list(reversed(range(16)))
    for i in range(80):
        for x in range(16):
            fb.line((x-8,0),(x,fb.height), color=colors[x])
        fb.show()
        # rotate colors
        colors = colors[1:] + colors[:1]
        time.sleep(0.04)

#########################################################################
# Other tests
#

@testing.automatic
def verify_cpu():
    fb = FrameBuffer(matrix_layout=[(0,0,0)])
    return testing.verify_cpu()
