'''
Automatic tests of gpio module via loopback output to input

Short GPIO 23 to 24.
'''
import testing_log
import importlib
import testing
import time
from threading import Timer
from functools import wraps

from rstem.gpio import Output, Input, PULL_UP, PULL_DOWN, PULL_DISABLE
from rstem.button import Button

OUTPUT_PIN = 23
INPUT_PIN = 24

MINIMUM_BUTTON_PRESS_PERIOD = 0.050
MINIMUM_INPUT_PERIOD = 0

def bo_setup(output_active_low=False, pull=None):
    def decorator(func):
        @wraps(func)
        def wrapper():
            # Setup
            b = Button(INPUT_PIN)
            o = Output(OUTPUT_PIN, active_low=output_active_low)

            passed = func(b, o)

            # Teardown
            b.disable()
            o.disable()

            return passed
        return wrapper
    return decorator

def io_setup(output_active_low=False, pull=None):
    def decorator(func):
        @wraps(func)
        def wrapper():
            # Setup
            i = Input(INPUT_PIN)
            o = Output(OUTPUT_PIN, active_low=output_active_low)

            passed = func(i, o)

            # Teardown
            i.disable()
            o.disable()

            return passed
        return wrapper
    return decorator

@testing.automatic
@bo_setup()
def bo_on_off_sequence(b, o):
    on_times = 0
    off_times = 0
    TRIES = 10
    for n in range(TRIES):
        o.on()
        time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
        if b.is_released:
            on_times += 1
        o.off()
        time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
        if b.is_pressed:
            off_times += 1
    passed = on_times == TRIES and off_times == TRIES
    if not passed:
        print("Failed: on_times {}, off_times {}, TRIES {}".format(on_times, off_times, TRIES))
    return passed

@testing.automatic
@bo_setup()
def button_is_pressed(b, o):
    o.off()
    time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
    return b.is_pressed()

@testing.automatic
@bo_setup()
def button_is_released(b, o):
    o.on()
    time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
    return b.is_released()

def try_n_half_presses(n, b, o):
    # Start with button released, and clear presses()
    o.on()
    time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
    b.presses()

    level = 0
    for i in range(n):
        o._set(level)
        time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
        level = 0 if level else 1

@testing.automatic
@bo_setup()
def button_0_half_presses(b, o):
    try_n_half_presses(0, b, o)
    return b.presses() == 0

@testing.automatic
@bo_setup()
def button_1_half_presses(b, o):
    try_n_half_presses(1, b, o)
    return b.presses() == 1

@testing.automatic
@bo_setup()
def button_2_half_presses(b, o):
    try_n_half_presses(2, b, o)
    return b.presses() == 1

@testing.automatic
@bo_setup()
def button_3_half_presses(b, o):
    try_n_half_presses(3, b, o)
    return b.presses() == 2

@testing.automatic
@bo_setup()
def button_4_half_presses(b, o):
    try_n_half_presses(4, b, o)
    return b.presses() == 2

@testing.automatic
@bo_setup()
def button_5_half_presses(b, o):
    try_n_half_presses(5, b, o)
    return b.presses() == 3

@testing.automatic
@bo_setup()
def button_6_half_presses(b, o):
    try_n_half_presses(6, b, o)
    return b.presses() == 3

@testing.automatic
@bo_setup()
def button_7_half_presses(b, o):
    try_n_half_presses(7, b, o)
    return b.presses() == 4

@testing.automatic
@bo_setup()
def button_8_half_presses(b, o):
    try_n_half_presses(8, b, o)
    return b.presses() == 4

@testing.automatic
@bo_setup()
def button_0_half_releases(b, o):
    try_n_half_presses(0, b, o)
    return b.presses(press=False) == 0

@testing.automatic
@bo_setup()
def button_1_half_releases(b, o):
    try_n_half_presses(1, b, o)
    return b.presses(press=False) == 0

@testing.automatic
@bo_setup()
def button_2_half_releases(b, o):
    try_n_half_presses(2, b, o)
    return b.presses(press=False) == 1

@testing.automatic
@bo_setup()
def button_3_half_releases(b, o):
    try_n_half_presses(3, b, o)
    return b.presses(press=False) == 1

@testing.automatic
@bo_setup()
def button_4_half_releases(b, o):
    try_n_half_presses(4, b, o)
    return b.presses(press=False) == 2

@testing.automatic
@bo_setup()
def button_5_half_releases(b, o):
    try_n_half_presses(5, b, o)
    return b.presses(press=False) == 2

@testing.automatic
@bo_setup()
def button_6_half_releases(b, o):
    try_n_half_presses(6, b, o)
    return b.presses(press=False) == 3

def _test_output_defaults_with_button():
    b = Button(INPUT_PIN)
    o = Output(OUTPUT_PIN) # default is active low!

    o.off() # HIGH
    time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
    released_worked = b.is_released() # Released button is HIGH
    o.on() # LOW
    time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
    pressed_worked = b.is_pressed() # PRESSED button is LOW

    b.disable()
    o.disable()
    return released_worked and pressed_worked

@testing.automatic
def output_defaults_with_button():
    return _test_output_defaults_with_button()

@testing.automatic
def button_recreation():
    # Recreate button pin several times and verify
    for i in range(5):
        button_in = Button(INPUT_PIN)
        button_out = Button(OUTPUT_PIN)
        button_in.disable()
        button_out.disable()

    return _test_output_defaults_with_button()

@testing.automatic
def button_invalid_pin():
    passed = False
    try:
        Button(28)
    except ValueError:
        passed = True
    return passed

def button_wait(b, o, press, push_time, timeout_time):
    def push():
        o.off()
        time.sleep(MINIMUM_BUTTON_PRESS_PERIOD)
        o.on()

    kwargs = {}
    if timeout_time:
        kwargs['timeout'] = timeout_time
    if press:
        kwargs['press'] = False

    o.on()
    # clear queue
    if isinstance(b, list):
        for button in b:
            button.presses()
    else:
        b.presses() 

    try:
        t = Timer(push_time, push)
        t.start()
        if isinstance(b, list):
            wait_ret = Button.wait_many(b, **kwargs)
        else:
            wait_ret = b.wait(**kwargs)
    finally:
        t.join()
    print("button wait returned: ", wait_ret)
    return wait_ret

@testing.automatic
@bo_setup()
def button_wait_press(b, o):
    wait_success = button_wait(b, o, press=True, push_time=0.2, timeout_time=None)
    return wait_success

@testing.automatic
@bo_setup()
def button_wait_release(b, o):
    wait_success = button_wait(b, o, press=False, push_time=0.2, timeout_time=None)
    return wait_success

@testing.automatic
@bo_setup()
def button_wait_with_timeout_failed(b, o):
    wait_success = button_wait(b, o, press=True, push_time=0.5, timeout_time=0.2)
    return not wait_success

@testing.automatic
@bo_setup()
def button_wait_with_timeout_success(b, o):
    wait_success = button_wait(b, o, press=True, push_time=0.2, timeout_time=0.5)
    return wait_success

@testing.automatic
@bo_setup()
def button_wait_button_list(b, o):
    which_button = button_wait([b], o, press=True, push_time=0.2, timeout_time=None)
    return which_button == 0

@testing.automatic
@bo_setup()
def button_wait_button_list_with_timeout(b, o):
    which_button = button_wait([b], o, press=True, push_time=0.5, timeout_time=0.2)
    return which_button == None

@testing.automatic
@io_setup()
def output_starts_off(i, o):
    time.sleep(MINIMUM_INPUT_PERIOD)
    return i.is_off()

@testing.automatic
@io_setup()
def output_turned_on(i, o):
    o.off()
    o.on()
    time.sleep(MINIMUM_INPUT_PERIOD)
    return i.is_on()

@testing.automatic
@io_setup()
def output_turned_off(i, o):
    o.on()
    o.off()
    time.sleep(MINIMUM_INPUT_PERIOD)
    return i.is_off()

@testing.automatic
@io_setup()
def io_on_off_sequence(i, o):
    on_times = 0
    off_times = 0
    TRIES = 10
    for n in range(TRIES):
        o.on()
        time.sleep(MINIMUM_INPUT_PERIOD)
        if i.is_off:
            on_times += 1
        o.off()
        time.sleep(MINIMUM_INPUT_PERIOD)
        if i.is_on:
            off_times += 1
    passed = on_times == TRIES and off_times == TRIES
    if not passed:
        print("Failed: on_times {}, off_times {}, TRIES {}".format(on_times, off_times, TRIES))
    return passed

@testing.automatic
@io_setup(output_active_low=True)
def output_init_active_low_on(i, o):
    o.on() # LOW
    time.sleep(MINIMUM_INPUT_PERIOD)
    return i.is_off()

@testing.automatic
@io_setup(output_active_low=True)
def output_init_active_low_off(i, o):
    o.off() # HIGH
    time.sleep(MINIMUM_INPUT_PERIOD)
    return i.is_on()

@testing.automatic
@io_setup(output_active_low=False)
def input_is_on(i, o):
    o.on()
    time.sleep(MINIMUM_INPUT_PERIOD)
    return i.is_on()

@testing.automatic
@io_setup(output_active_low=False)
def input_is_off(i, o):
    o.off()
    time.sleep(MINIMUM_INPUT_PERIOD)
    return i.is_off()

def _test_output_defaults_with_input():
    i = Input(INPUT_PIN)
    o = Output(OUTPUT_PIN) # default is active low!

    o.off() # HIGH
    time.sleep(MINIMUM_INPUT_PERIOD)
    high_worked = i.is_on()
    o.on() # LOW
    time.sleep(MINIMUM_INPUT_PERIOD)
    low_worked = i.is_off()

    i.disable()
    o.disable()
    return high_worked and low_worked

@testing.automatic
def output_defaults_with_input():
    return _test_output_defaults_with_input()

@testing.automatic
def input_recreation():
    # Recreate input pin several times and verify
    for i in range(5):
        i1 = Input(INPUT_PIN)
        i2 = Input(OUTPUT_PIN)
        i1.disable()
        i2.disable()

    return _test_output_defaults_with_input()

@testing.automatic
def input_invalid_pin():
    passed = False
    try:
        Input(28)
    except ValueError:
        passed = True
    return passed

@testing.automatic
@io_setup()
def time_output(i, o):
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

def input_pull_test(pull, stayed_on, stayed_off, configure=False):
    for n in range(5):
        if configure:
            i = Input(INPUT_PIN)
            i.configure(pull=pull)
        else:
            i = Input(INPUT_PIN, pull=pull)
        o = Output(OUTPUT_PIN, active_low=False)
        o.on()
        o.disable()
        actually_stayed_on = i.is_on()
        o = Output(OUTPUT_PIN, active_low=False)
        o.off()
        o.disable()
        actually_stayed_off = i.is_off()
        i.disable()
        if stayed_on == actually_stayed_on and stayed_off == actually_stayed_off:
            return True
        time.sleep(0.5)
        print("FAILED, RETRYING...")
    print("TOO MANY RETRIES!")
    return False

@testing.automatic
def input_pull_down():
    return input_pull_test(PULL_DOWN, stayed_on=False, stayed_off=True)
    
@testing.automatic
def input_pull_up():
    return input_pull_test(PULL_UP, stayed_on=True, stayed_off=False)

@testing.automatic
def input_pull_disable():
    return input_pull_test(PULL_DISABLE, stayed_on=True, stayed_off=True)
    
@testing.automatic
def input_pull_down_via_configure():
    return input_pull_test(PULL_DOWN, stayed_on=False, stayed_off=True, configure=True)
    
@testing.automatic
def input_pull_up_via_configure():
    return input_pull_test(PULL_UP, stayed_on=True, stayed_off=False, configure=True)

@testing.automatic
def input_pull_disable_via_configure():
    return input_pull_test(PULL_DISABLE, stayed_on=True, stayed_off=True, configure=True)
    
@testing.automatic
@io_setup()
def verify_cpu(i, o):
    return testing.verify_cpu()
