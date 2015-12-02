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
count = 0
FLASH_COUNT = 3
flash_lit = True
while True:
    pos = mc.player.getTilePos()
    flashing = False
    x = round(pos.x/25 + 3.5)
    if not 0 <= x <= 7:
        flashing = True
    x = min(7, max(0, x))
    z = round(pos.z/25 + 3.5)
    if not 0 <= z <= 7:
        flashing = True
    z = min(7, max(0, z))

    fb.erase()
    count += 1
    if count > FLASH_COUNT:
        flash_lit = not flash_lit
        count = 0
    if not flashing or flashing and flash_lit:
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


