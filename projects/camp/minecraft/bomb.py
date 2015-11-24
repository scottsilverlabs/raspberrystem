from rstem.accel import Accel
from rstem.button import Button
from rstem.mcpi import minecraft, control, block
from rstem.mcpi.vec3 import Vec3
import time
from math import sin, cos, radians

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()
button = Button(7)

def detonate(mc, pos, radius=1):
    r_vector = Vec3(radius,radius,radius)
    mc.setBlocks(pos - r_vector, pos + r_vector, block.AIR)

place_mode = True
while True:
    if place_mode:
        if button.presses():
            control.hit()
        hits = mc.events.pollBlockHits()
        if hits:
            tnt_pos = hits[0].pos
            mc.setBlock(tnt_pos, block.TNT)
            place_mode = False

    else:
        if button.presses():
            detonate(mc, tnt_pos)
            place_mode = True

    time.sleep(0.01)

