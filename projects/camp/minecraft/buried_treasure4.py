from rstem.accel import Accel
from rstem.button import Button
from rstem.led_matrix import FrameBuffer, Sprite
from rstem.mcpi import minecraft, control, block
import time
from random import randint
from math import atan2, degrees

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()

ARENA_WIDTH = 10
GOLD_DEPTH = 2
gold_pos = mc.player.getTilePos()
gold_pos.x +=  randint(-ARENA_WIDTH, ARENA_WIDTH)
gold_pos.z +=  randint(-ARENA_WIDTH, ARENA_WIDTH)
gold_pos.y = mc.getHeight(gold_pos.x, gold_pos.z) - GOLD_DEPTH
mc.setBlock(gold_pos, block.GOLD_BLOCK)

keymap = {
    Button(23) : control.left,
    Button(14) : control.right,
    Button(18) : control.forward,
    Button(15) : control.backward,
    Button(7)  : control.smash,
    }

accel = Accel()

arrow0deg = Sprite("""
    --------
    --------
    -----F--
    ------F-
    FFFFFFFF
    ------F-
    -----F--
    --------
    """)
arrow15deg = Sprite("""
    --------
    -----F--
    ------F-
    ----FFFF
    FFFF--F-
    -----F--
    --------
    --------
    """)
arrow30deg = Sprite("""
    --------
    ----FFFF
    ------FF
    ----FF-F
    ---F---F
    -FF-----
    F-------
    --------
    """)
arrow45deg = Sprite("""
    ----FFFF
    ------FF
    -----F-F
    ----F--F
    ---F----
    --F-----
    -F------
    F-------
    """)

arrow60deg = Sprite(arrow30deg).flip().rotate(-90)
arrow75deg = Sprite(arrow15deg).flip().rotate(-90)
arrows = [
    Sprite(arrow0deg).rotate(0),
    Sprite(arrow15deg).rotate(0),
    Sprite(arrow30deg).rotate(0),
    Sprite(arrow45deg).rotate(0),
    Sprite(arrow60deg).rotate(0),
    Sprite(arrow75deg).rotate(0),
    Sprite(arrow0deg).rotate(90),
    Sprite(arrow15deg).rotate(90),
    Sprite(arrow30deg).rotate(90),
    Sprite(arrow45deg).rotate(90),
    Sprite(arrow60deg).rotate(90),
    Sprite(arrow75deg).rotate(90),
    Sprite(arrow0deg).rotate(180),
    Sprite(arrow15deg).rotate(180),
    Sprite(arrow30deg).rotate(180),
    Sprite(arrow45deg).rotate(180),
    Sprite(arrow60deg).rotate(180),
    Sprite(arrow75deg).rotate(180),
    Sprite(arrow0deg).rotate(270),
    Sprite(arrow15deg).rotate(270),
    Sprite(arrow30deg).rotate(270),
    Sprite(arrow45deg).rotate(270),
    Sprite(arrow60deg).rotate(270),
    Sprite(arrow75deg).rotate(270),
    ]

def vector_angle(start, end):
    return degrees(atan2(end.x - start.x, end.z - start.z))
    
compass = Button(24)
fb = FrameBuffer()
while block.Block(mc.getBlock(gold_pos)) == block.GOLD_BLOCK:
    if compass.presses():
        heading = control.get_heading(mc)
        angle_to_gold = vector_angle(mc.player.getPos(), gold_pos)
        compass_angle = 90 + (angle_to_gold - heading)
        fb.erase()
        arrow_index = round(compass_angle/15) % 24
        fb.draw(arrows[arrow_index])
        fb.show()

    for button, action in keymap.items():
        if button.is_pressed():
            action()
        else:
            action(release=True)

    x, y, z = accel.forces()
    control.look(up=20*y, left=20*x)
    
    time.sleep(0.01)

mc.postToChat("You found the gold!")
time.sleep(3)


