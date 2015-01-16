import testing_log
import importlib
import testing
import pytest
import time
from threading import Timer
from functools import wraps

from rstem import accel

'''
Automatic tests of accel module

Accelerometer must be connected via VCC, GND, SDA and SCL.  Accelerometer must
sit level (flat) in the X/Y directions.
'''

def io_setup(output_active_low=False, pull=None):
    def decorator(func):
        @wraps(func)
        def wrapper():
            a = accel.Accel()

            passed = func(a)

            return passed
        return wrapper
    return decorator

@testing.automatic
@io_setup()
def accel_get_pos(a):
    x, y, z = a.angles()
    x_good = abs(0.0 - x) < 3.0
    y_good = abs(0.0 - y) < 3.0
    z_good = abs(90.0 - z) < 3.0
    return x_good and y_good and z_good

