import testing
import rstem.led_matrix as led

'''
Automatic API tests for LED Matrix.
'''

def erased_fb(fb):
    allzero = True
    for row in fb:
        for point in row:
            if point != 0: allzero = False
    return allzero
    
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
def init_matrices():
    led.init_matrices()
    return True

@testing.automatic
def test_erased_fb():
    led.init_matrices()
    return erased_fb(led._framebuffer())

@testing.automatic
def point1():
    return point_test(0, 0, 1)

@testing.automatic
def point2():
    return point_test(1, 2, 3)

@testing.automatic
def point3():
    return point_test(7, 7, 10)

@testing.automatic
def point_out_of_bounds1():
    return out_of_bounds_point_test(-1, 0)

@testing.automatic
def point_out_of_bounds2():
    return out_of_bounds_point_test(0, -1)

@testing.automatic
def point_out_of_bounds3():
    return out_of_bounds_point_test(led.width, 0)

@testing.automatic
def point_out_of_bounds4():
    return out_of_bounds_point_test(0, led.height)
