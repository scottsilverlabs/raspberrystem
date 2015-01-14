import testing_log
import importlib
import testing
import pytest
import rstem.gpio as g
import time
from threading import Timer
from functools import wraps

'''
Automatic tests of gpio module via loopback output to input

Short GPIO 23 to 24.
'''

OUTPUT_PIN = 23
INPUT_PIN = 24

def io_setup(output_active_low=False, pull=None):
    def decorator(func):
        @wraps(func)
        def wrapper():
            # Setup
            b = g.Button(INPUT_PIN)
            o = g.Output(OUTPUT_PIN, active_low=output_active_low)

            passed = func(b, o)

            # Teardown
            g.DisabledPin(OUTPUT_PIN)
            g.DisabledPin(INPUT_PIN)

            return passed
        return wrapper
    return decorator

@testing.automatic
@io_setup()
def output_starts_off(b, o):
    return b.is_pressed()

@testing.automatic
@io_setup()
def output_turned_on(b, o):
    o.off()
    o.on()
    return b.is_released()

@testing.automatic
@io_setup()
def output_turned_off(b, o):
    o.on()
    o.off()
    return b.is_pressed()

@testing.automatic
@io_setup()
def output_turned_on_via_set(b, o):
    o.off()
    o.level = 1
    return b.is_released()

@testing.automatic
@io_setup()
def output_turned_off_via_set(b, o):
    o.on()
    o.level = 0
    return b.is_pressed()

@testing.automatic
@io_setup()
def io_on_off_sequence(b, o):
    on_times = 0
    off_times = 0
    TRIES = 10
    for n in range(TRIES):
        o.on()
        time.sleep(0.050)
        if b.is_released:
            on_times += 1
        o.off()
        time.sleep(0.050)
        if b.is_pressed:
            off_times += 1
    passed = on_times == TRIES and off_times == TRIES
    if not passed:
        print("Failed: on_times {}, off_times {}, TRIES {}".format(on_times, off_times, TRIES))
    return passed

""" TBD:
@testing.automatic
@io_setup()
def output_init_start_off_false(b, o):
    # Create output that starts HIGH
    return False
"""

@testing.automatic
@io_setup(output_active_low=True)
def output_init_active_low_on(b, o):
    o.on()
    return b.is_pressed()

@testing.automatic
@io_setup(output_active_low=True)
def output_init_active_low_off(b, o):
    o.off()
    return b.is_released()

@testing.automatic
@io_setup()
def button_is_pressed(b, o):
    o.off()
    return b.is_pressed()

@testing.automatic
@io_setup()
def button_is_released(b, o):
    o.on()
    return b.is_released()

MINIMUM_BUTTON_PRESS_PERIOD = 0.050
def try_n_half_presses(n, b, o):
    # Start with button released, and clear presses()
    o.level = 1
    time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
    b.presses()

    level = 0
    for i in range(n):
        o.level = level
        time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
        level = 0 if level else 1

@testing.automatic
@io_setup()
def button_0_half_presses(b, o):
    try_n_half_presses(0, b, o)
    return b.presses() == 0

@testing.automatic
@io_setup()
def button_1_half_presses(b, o):
    try_n_half_presses(1, b, o)
    return b.presses() == 1

@testing.automatic
@io_setup()
def button_2_half_presses(b, o):
    try_n_half_presses(2, b, o)
    return b.presses() == 1

@testing.automatic
@io_setup()
def button_3_half_presses(b, o):
    try_n_half_presses(3, b, o)
    return b.presses() == 2

@testing.automatic
@io_setup()
def button_4_half_presses(b, o):
    try_n_half_presses(4, b, o)
    return b.presses() == 2

@testing.automatic
@io_setup()
def button_5_half_presses(b, o):
    try_n_half_presses(5, b, o)
    return b.presses() == 3

@testing.automatic
@io_setup()
def button_6_half_presses(b, o):
    try_n_half_presses(6, b, o)
    return b.presses() == 3

@testing.automatic
@io_setup()
def button_7_half_presses(b, o):
    try_n_half_presses(7, b, o)
    return b.presses() == 4

@testing.automatic
@io_setup()
def button_8_half_presses(b, o):
    try_n_half_presses(8, b, o)
    return b.presses() == 4

@testing.automatic
@io_setup()
def button_0_half_releases(b, o):
    try_n_half_presses(0, b, o)
    return b.releases() == 0

@testing.automatic
@io_setup()
def button_1_half_releases(b, o):
    try_n_half_presses(1, b, o)
    return b.releases() == 0

@testing.automatic
@io_setup()
def button_2_half_releases(b, o):
    try_n_half_presses(2, b, o)
    return b.releases() == 1

@testing.automatic
@io_setup()
def button_3_half_releases(b, o):
    try_n_half_presses(3, b, o)
    return b.releases() == 1

@testing.automatic
@io_setup()
def button_4_half_releases(b, o):
    try_n_half_presses(4, b, o)
    return b.releases() == 2

@testing.automatic
@io_setup()
def button_5_half_releases(b, o):
    try_n_half_presses(5, b, o)
    return b.releases() == 2

@testing.automatic
@io_setup()
def button_6_half_releases(b, o):
    try_n_half_presses(6, b, o)
    return b.releases() == 3

@testing.automatic
def button_recreation():
    # Recreate button pin serval times and verify
    for i in range(5):
        g.Button(INPUT_PIN)
        g.Button(OUTPUT_PIN)
        g.DisabledPin(INPUT_PIN)
        g.DisabledPin(OUTPUT_PIN)

    b = g.Button(INPUT_PIN)
    o = g.Output(OUTPUT_PIN)

    o.on()
    released_worked = b.is_released()
    o.off()
    pressed_worked = b.is_pressed()

    g.DisabledPin(OUTPUT_PIN)
    g.DisabledPin(INPUT_PIN)
    return released_worked and pressed_worked

@testing.automatic
def button_invalid_pin():
    passed = False
    try:
        g.Button(5)
    except ValueError:
        passed = True
    return passed

@testing.automatic
@io_setup()
def time_output(b, o):
    TRIES = 100
    start = time.time()
    for n in range(TRIES):
        o.on()
    end = time.time()
    rate = float(TRIES)/(end-start)
    # We expect this to run at least MINIMUM_RATE in Hz.  Arbitrary, just to
    # keep it reasonable (testing shows it runs at ~3kHz).
    MINIMUM_RATE = 1000
    print("Output test running at: {:.2f}Hz (MINIMUM_RATE: {}Hz)".format(rate, MINIMUM_RATE))
    return rate > MINIMUM_RATE

