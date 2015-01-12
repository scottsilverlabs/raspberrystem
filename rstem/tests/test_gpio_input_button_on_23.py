import testing_log
import importlib
import testing
import pytest
import rstem.gpio as g
import time

'''
Connect a button from GPIO 23 to Ground
'''

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

@testing.automatic
def dummy_exc_test():
    return True

