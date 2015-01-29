import testing
import time
from functools import partial
from rstem.led_matrix import FrameBuffer

'''
Automatic API tests for LED Matrix.
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
    return timeit(partial(fb.point, 0, 0)) > 8000

@testing.automatic
def time_point2():
    fb = FrameBuffer(matrix_list=[(0,0)])
    timeit(partial(fb.point2, 0, 0))
    return False

@testing.automatic
def time_show():
    fb = FrameBuffer(matrix_list=[(0,0)])
    timeit(partial(fb.show), loops=1000)
    return False

@testing.automatic
def time_newshow():
    fb = FrameBuffer(matrix_list=[(0,0)])
    timeit(partial(fb.newshow), loops=1000)
    return False

@testing.automatic
def time_show2():
    fb = FrameBuffer(matrix_list=[(0,0)])
    timeit(partial(fb.show2), loops=1000)
    return False

@testing.automatic
def time_show2_only():
    fb = FrameBuffer(matrix_list=[(0,0)])
    timeit(partial(fb.show2_only), loops=1000)
    return False

