'''
Automatic tests of accel module

Accelerometer must be connected via VCC, GND, SDA and SCL.  Accelerometer must
sit level (flat) in the X/Y directions.
'''
import testing_log
import importlib
import testing
import time
from threading import Timer
from functools import wraps

from rstem import accel

def io_setup():
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
def accel_forces(a):
    x, y, z = a.forces()
    x_good = abs(0.0 - x) < 0.05
    y_good = abs(0.0 - y) < 0.05
    z_good = abs(1.0 - z) < 0.05
    print("Note: Accelerometer should be sitting flat , with Z pointing up.")
    print("X: {}".format(x))
    print("Y: {}".format(y))
    print("Z: {}".format(z))
    return x_good and y_good and z_good

@testing.automatic
@io_setup()
def accel_time_forces(a):
    TRIES = 100
    start = time.time()
    for n in range(TRIES):
        x, y, z = a.forces()
    end = time.time()
    rate = float(TRIES)/(end-start)
    # We expect this to run at least MINIMUM_RATE in Hz.  Arbitrary, just to
    # keep it reasonable (testing shows it runs at ~300Hz).
    MINIMUM_RATE = 100
    print("Output test running at: {:.2f}Hz (MINIMUM_RATE: {}Hz)".format(rate, MINIMUM_RATE))
    return rate > MINIMUM_RATE

@testing.manual
@io_setup()
def accel_vertical(a):
    '''Accelerometer should be sitting vertically, with Y pointing up.
    '''
    x, y, z = a.forces()
    x_good = abs(0.0 - x) < 0.05
    y_good = abs(1.0 - y) < 0.05
    z_good = abs(0.0 - z) < 0.05
    print("X: {}".format(x))
    print("Y: {}".format(y))
    print("Z: {}".format(z))
    return x_good and y_good and z_good

