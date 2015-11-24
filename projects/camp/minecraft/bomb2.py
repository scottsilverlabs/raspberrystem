from rstem.accel import Accel
from rstem.button import Button
from rstem.mcpi import minecraft, control, block
from rstem.mcpi.vec3 import Vec3
from rstem.led_matrix import FrameBuffer, Text
from rstem.sound import Sound
import time
from math import sin, cos, radians

fb = FrameBuffer()

bomb_sound = Sound("fire.wav")

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()
bomb = Button(7)
up = Button(18)
down = Button(15)

def detonate(mc, pos, radius=1):
    r_vector = Vec3(radius,radius,radius)
    mc.setBlocks(pos - r_vector, pos + r_vector, block.AIR)
    bomb_sound.play()

place_mode = True
radius = 1
while True:
    if place_mode:
        if bomb.presses():
            control.hit()
        hits = mc.events.pollBlockHits()
        if hits:
            tnt_pos = hits[0].pos
            mc.setBlock(tnt_pos, block.TNT)
            place_mode = False

    else:
        if bomb.presses():
            detonate(mc, tnt_pos, radius)
            place_mode = True

    radius += up.presses()
    radius -= down.presses()
    radius = max(min(9, radius), 0)

    fb.erase()
    fb.draw(Text(str(radius)))
    fb.show()

    time.sleep(0.01)

