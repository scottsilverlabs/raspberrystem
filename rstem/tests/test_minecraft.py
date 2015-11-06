'''
Tests of minecraft API

No hardware requirements.  Minecraft must be started and in-world before running.
'''
import testing
from subprocess import call, Popen, PIPE
from functools import partial, wraps
from rstem.mcpi import minecraft, vec3, block
from rstem.mcpi import control
import time
from math import atan2, degrees

shcall = partial(call, shell=True)
shopen = partial(Popen, stdin=PIPE, stderr=PIPE, stdout=PIPE, close_fds=True, shell=True)

MINECRAFT_WIN_NAME = 'Minecraft - Pi edition'
XDOTOOL_CMD = "DISPLAY=:0 xdotool search --name '{:s}' ".format(MINECRAFT_WIN_NAME)
HIDE_WIN_CMD = "DISPLAY=:0 wmctrl -r '{:s}' -b add,hidden".format(MINECRAFT_WIN_NAME)
SHOW_WIN_CMD = "DISPLAY=:0 wmctrl -a '{:s}'".format(MINECRAFT_WIN_NAME)
MINECRAFT_CMD = "DISPLAY=:0 /usr/bin/minecraft-pi >/dev/null &"
KILL_MINECRAFT_CMD = "killall minecraft-pi 2>/dev/null"
IS_RUNNING_MINECRAFT_CMD = "pgrep '^minecraft-pi$' >/dev/null"

BOX_WIDTH = 10
BOX_HEIGHT = 3

shcall(KILL_MINECRAFT_CMD)
def start_minecraft(quit=True, in_box=False):
    def decorator(func):
        @wraps(func)
        def wrapper():
            # Setup
            time.sleep(0.5)
            if shcall(IS_RUNNING_MINECRAFT_CMD):
                shcall(MINECRAFT_CMD)
                time.sleep(0.5)
                show(False)

            if not window_visible(get_wid()):
                show(True)
                time.sleep(0.5)
                shcall(XDOTOOL_CMD + "key Return")
                shcall(XDOTOOL_CMD + "key Return")
                time.sleep(3)

            if in_box:
                mc = minecraft.Minecraft.create()

                mc.setBlocks(0, 0, 0, BOX_WIDTH, BOX_HEIGHT-1, BOX_WIDTH, block.BRICK_BLOCK)
                mc.setBlocks(0, BOX_HEIGHT, 0, BOX_WIDTH, 128, BOX_WIDTH, block.AIR)
                mc.setBlocks(1, 1, 1, BOX_WIDTH-1, BOX_HEIGHT, BOX_WIDTH-1, block.AIR)
                mc.player.setTilePos(int(BOX_WIDTH)/2, 1, int(BOX_WIDTH)/2)
            
                a = mc.player.getPos()
                angle_to_x = 999
                while abs(angle_to_x) > 0.3:
                    mc.player.setTilePos(a)
                    control.forward(0.1)
                    b = mc.player.getPos()
                    angle_to_x = degrees(atan2((b.x - a.x),(b.z - a.z)))
                    control.look(right=int(angle_to_x*5))
                LOOK_TO_CENTER_DIST = 423
                LOOK_UP_MAX = 2000
                control.look(up=LOOK_UP_MAX)
                control.look(up=-LOOK_TO_CENTER_DIST)

            passed = func()

            # Teardown
            if quit:
                show(False)
                shcall(KILL_MINECRAFT_CMD)

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
def action_toggle_fly():
    '''Verify that the player flies up and then drops'''
    mc = minecraft.Minecraft.create()

    # Create tower of air above us
    pos = mc.player.getTilePos()
    for y in range(30):
        mc.setBlock(vec3.Vec3(0, y, 0) + pos, block.AIR)
    time.sleep(1)

    control.toggle_fly_mode()
    control.jump(duration=1)
    time.sleep(1.2)
    control.toggle_fly_mode()
    time.sleep(5)

@testing.debug
@start_minecraft(quit=False, in_box=True)
def move_backward():
    mc = minecraft.Minecraft.create()
    control.backward(1.5)
    pos = mc.player.getTilePos()
    print(pos)
    return (pos.x, pos.y, pos.z) == (5, 1, 1)




