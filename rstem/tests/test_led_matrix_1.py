import testing_log
import importlib
import testing
import rstem.led_matrix as led
import time

@testing.manual_output
def vertical_bars():
    '''A vertical bar on the LED Matrix moving from far left to far right in about 1 second.
    '''
    led.init_grid()
    for x in range(8):
        led.erase()
        led.line((x,0),(x,7))
        led.show()
        time.sleep(0.1)

@testing.manual_output
def horizontal_bars():
    '''A horizontal bar on the LED Matrix moving from bottom to top in about 1 second.
    '''
    vdjksfnv
    led.init_grid()
    for y in range(8):
        led.erase()
        led.line((0,y),(7,y))
        led.show()
        time.sleep(0.1)

@testing.automatic
def dummy_exc_test():
    assert False
    return True

@testing.automatic
def dummy_fail_test():
    return False

@testing.automatic
def dummy_test():
    return True

