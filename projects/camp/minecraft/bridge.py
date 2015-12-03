from rstem.button import Button
from rstem.mcpi import minecraft, control, block
from rstem.mcpi.vec3 import Vec3
import time
from math import sin, cos, radians

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()
button = Button(7)

while True:
    if button.presses():
        heading = control.get_heading(mc)
        x_delta = sin(radians(heading))
        z_delta = cos(radians(heading))
        pos = mc.player.getPos() - Vec3(0, 1, 0)
        for i in range(100):
            pos += Vec3(x_delta, 0, z_delta)
            mc.setBlock(pos, block.STONE)

    time.sleep(0.01)

