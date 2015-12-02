from rstem.accel import Accel
from rstem.button import Button
from rstem.led_matrix import FrameBuffer, Sprite
from rstem.mcpi import minecraft, control, block
from rstem.mcpi.vec3 import Vec3
from rstem.sound import Note
import time
from random import randint
from math import atan2, degrees

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()

keymap = {
    Button(23) : control.left,
    Button(14) : control.right,
    Button(18) : control.forward,
    Button(15) : control.backward,
    Button(7)  : control.smash,
    }

accel = Accel()

fb = FrameBuffer()
while True:
    pos = mc.player.getTilePos()
    x = round(pos.x/25 + 3.5)
    x = min(fb.width-1, max(0, x))
    z = round(pos.z/25 + 3.5)
    z = min(fb.width-1, max(0, z))
    fb.erase()
    fb.point(z, x)
    fb.show()

    for button, action in keymap.items():
        if button.is_pressed():
            action()
        else:
            action(release=True)

    x, y, z = accel.forces()
    control.look(up=20*y, left=20*x)
    
    time.sleep(0.01)


