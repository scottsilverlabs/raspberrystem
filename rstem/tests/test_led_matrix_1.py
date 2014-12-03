import testing_log
import importlib
import testing
import pytest
import rstem.led_matrix as led
import time

'''
Handle:
    collect up all tests and print agenda
    shortest possible lines to write a test
    common setup/teardown functions
    - manual output test
        catch all exception and fail test
        Hit enter to start
        pass/fail/skip/retry
    - manual input test
        - function repeatedly called.  must return true within timeout time.
        - outcome: pass/fail/timeout
        - print exception
    - special test to handle forced exceptions
    - print test summary
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

@testing.manual_output
def horizontal_bars():
    '''A horizontal bar on the LED Matrix moving from top to bottom in about 1 second.
    '''
    led.init_grid()
    for x in range(8):
        led.erase()
        led.line((x,0),(x,7))
        led.show()
        time.sleep(0.1)

