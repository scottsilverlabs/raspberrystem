'''
Tests of minecraft API

No hardware requirements.  Minecraft must be started and in-world before running.
'''
import testing
from subprocess import call, Popen, PIPE
from functools import partial, wraps
from rstem.mcpi import minecraft
from rstem.mcpi import control
import time

shcall = partial(call, shell=True)
shopen = partial(Popen, stdin=PIPE, stderr=PIPE, stdout=PIPE, close_fds=True, shell=True)

MINECRAFT_WIN_NAME = 'Minecraft - Pi edition'
XDOTOOL_CMD = "DISPLAY=:0 xdotool search --name '{:s}'".format(MINECRAFT_WIN_NAME)
HIDE_WIN_CMD = "DISPLAY=:0 wmctrl -r '{:s}' -b add,hidden".format(MINECRAFT_WIN_NAME)
SHOW_WIN_CMD = "DISPLAY=:0 wmctrl -a '{:s}'".format(MINECRAFT_WIN_NAME)
MINECRAFT_CMD = "DISPLAY=:0 /usr/bin/minecraft-pi >/dev/null &"
KILL_MINECRAFT_CMD = "killall minecraft-pi 2>/dev/null"
IS_RUNNING_MINECRAFT_CMD = "pgrep '^minecraft-pi$' >/dev/null"

shcall(KILL_MINECRAFT_CMD)

def start_minecraft(quit=True):
    def decorator(func):
        @wraps(func)
        def wrapper():
            # Setup
            if shcall(IS_RUNNING_MINECRAFT_CMD):
                shcall(MINECRAFT_CMD)
                time.sleep(0.5)
                show(False)

            passed = func()

            # Teardown
            if quit:
                shcall(KILL_MINECRAFT_CMD)

            return passed
        return wrapper
    return decorator

def show_minecraft(hide=True):
    def decorator(func):
        @wraps(func)
        def wrapper():
            # Setup
            if not window_visible(get_wid()):
                show(True)
                time.sleep(0.5)
                shcall(XDOTOOL_CMD + " key Return")
                shcall(XDOTOOL_CMD + " key Return")
                time.sleep(2)

            passed = func()

            # Teardown
            if hide:
                show(False)

            return passed
        return wrapper
    return decorator

def window_visible(wid):
    cmd = "DISPLAY=:0 xwininfo -stats -id {:d} | awk -F: '/Map State/{{print $2}}'".format(wid)
    mapped = shopen(cmd).stdout.read().strip().decode()
    if mapped == 'IsViewable':
        return True
    elif mapped != 'IsUnMapped':
        raise IOError('Cannot detect if window is mapped or not')
    return False

def get_wid():
    return int(shopen(XDOTOOL_CMD).stdout.read().strip())

def show(show):
    shcall(SHOW_WIN_CMD if show else HIDE_WIN_CMD)

@testing.automatic
def show_fails_if_minecraft_not_running():
    shcall(KILL_MINECRAFT_CMD)
    time.sleep(0.5)

    try:
        control.show()
    except IOError:
        return True

    return False

@testing.automatic
@start_minecraft()
def show_opens():
    wid = get_wid()
    show(False)

    time.sleep(0.5)
    if window_visible(wid):
        print('FAILED: Window should NOT be viewable, but it is')
        return False
    else:
        print('PASSED: Window should NOT be viewable, and it is not')

    control.show()

    time.sleep(0.5)
    if window_visible(wid):
        print('PASSED: Window SHOULD be viewable, and it is')
    else:
        print('FAILED: Window SHOULD be viewable, but it is NOT')
        return False

    return True

@testing.automatic
@start_minecraft()
def hide_closes():
    wid = get_wid()
    show(True)

    time.sleep(0.5)
    if window_visible(wid):
        print('PASSED: Window SHOULD be viewable, and it is')
    else:
        print('FAILED: Window SHOULD be viewable, but it is NOT')
        return False

    control.hide()

    time.sleep(0.5)
    if window_visible(wid):
        print('FAILED: Window should NOT be viewable, but it is')
        return False
    else:
        print('PASSED: Window should NOT be viewable, and it is not')

    return True

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_forward_then_stop():
    '''Verify that the player moves forward for a half second'''
    control.forward()
    time.sleep(0.5)
    control.stop()
    time.sleep(0.5)

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_backward_half_second():
    '''Verify that the player does a 'backward' move for a half second'''
    control.backward(duration=0.5)
    time.sleep(1)

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_forward_half_second():
    '''Verify that the player does a 'forward' move for a half second'''
    control.forward(duration=0.5)
    time.sleep(1)

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_jump_half_second():
    '''Verify that the player does a 'jump' move for a half second'''
    control.jump(duration=0.5)
    time.sleep(1)

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_crouch_half_second():
    '''Verify that the player does a 'crouch' move for a half second'''
    control.crouch(duration=0.5)
    time.sleep(1)

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_left_half_second():
    '''Verify that the player does a 'left' move for a half second'''
    control.left(duration=0.5)
    time.sleep(1)

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_right_half_second():
    '''Verify that the player does a 'right' move for a half second'''
    control.right(duration=0.5)
    time.sleep(1)

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_ascend_half_second():
    '''Verify that the player does a 'ascend' move for a half second'''
    control.ascend(duration=0.5)
    time.sleep(1)

@testing.manual_output
@start_minecraft(quit=False)
@show_minecraft(hide=False)
def move_descend_half_second():
    '''Verify that the player does a 'descend' move for a half second'''
    control.descend(duration=0.5)
    time.sleep(1)

