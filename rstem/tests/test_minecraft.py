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

def start_minecraft():
    def decorator(func):
        @wraps(func)
        def wrapper():
            # Setup
            shcall(KILL_MINECRAFT_CMD)
            shcall(MINECRAFT_CMD)
            time.sleep(0.5)

            passed = func()

            # Teardown
            shcall(KILL_MINECRAFT_CMD)

            return passed
        return wrapper
    return decorator

def show_minecraft():
    def decorator(func):
        @wraps(func)
        def wrapper():
            # Setup
            show(True)
            time.sleep(0.5)

            passed = func()

            # Teardown
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

XDOTOOL_CMD = "DISPLAY=:0 xdotool search --name 'Minecraft - Pi edition'"
MINECRAFT_CMD = "DISPLAY=:0 /usr/bin/minecraft-pi &"
KILL_MINECRAFT_CMD = "killall minecraft-pi 2>/dev/null"

def get_wid():
    return int(shopen(XDOTOOL_CMD).stdout.read().strip())

def show(show):
    shcall(XDOTOOL_CMD + " {:s} --sync".format("windowmap" if show else "windowunmap"))

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

