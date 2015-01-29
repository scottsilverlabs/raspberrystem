import testing
import rstem.led_matrix as led

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
    rows = list(reversed(rows))
    return rows

def erased_fb(fb):
    return makefb('00000000\n' * 8)
    
def point_test(x, y, color):
    led.init_matrices()

    led.point(x, y, color)
    fb = led._framebuffer()
    goodpoint = fb[x][y] == color

    # set point to 0, and verify all points are 0.
    fb[x][y] = 0
    erased = erased_fb(fb)

    return goodpoint and erased

def out_of_bounds_point_test(x, y):
    led.init_matrices()
    led.point(x, y, 1)
    return erased_fb(led._framebuffer())

@testing.automatic
def __old__init_matrices():
    led.init_matrices()
    makefb('''
        12345678
        22223456
        33334567
        44445678
        55556789
        6666789a
        777789ab
        88889abc''')
    return True

@testing.automatic
def __old__test_erased_fb():
    led.init_matrices()
    return erased_fb(led._framebuffer())

@testing.automatic
def __old__point1():
    return point_test(0, 0, 1)

@testing.automatic
def __old__point2():
    return point_test(1, 2, 3)

@testing.automatic
def __old__point3():
    return point_test(7, 7, 10)

@testing.automatic
def __old__point_out_of_bounds1():
    return out_of_bounds_point_test(-1, 0)

@testing.automatic
def __old__point_out_of_bounds2():
    return out_of_bounds_point_test(0, -1)

@testing.automatic
def __old__point_out_of_bounds3():
    return out_of_bounds_point_test(led.width, 0)

@testing.automatic
def __old__point_out_of_bounds4():
    return out_of_bounds_point_test(0, led.height)
