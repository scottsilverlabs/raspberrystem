import testing
import rstem.led_matrix as led

'''
Automatic API tests for LED Matrix.
'''

@testing.automatic
def init_matrices():
    led.init_matrices()
    return True

@testing.automatic
def empty_fb():
    led.init_matrices()
    x = led._framebuffer()
    print(x)
    return True

def point_test(x, y, color):
    led.init_matrices()

    led.point(x, y, color)
    fb = led._framebuffer()
    goodpoint = fb[x][y] == color

    # set point to 0, and verify all points are 0.
    fb[x][y] = 0
    allzero = True
    for row in fb:
        for p in row:
            if p != 0: allzero = False

    return goodpoint and allzero

@testing.automatic
def point1():
    return point_test(0, 0, 1)

@testing.automatic
def point2():
    return point_test(1, 2, 3)

@testing.automatic
def point3():
    return point_test(7, 7, 10)

