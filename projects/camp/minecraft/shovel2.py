from rstem.button import Button
from rstem.mcpi import minecraft, control, block
from rstem.mcpi.vec3 import Vec3
import time

control.show(hide_at_exit=True)
mc = minecraft.Minecraft.create()
button = Button(7)

def dig(mc, pos, radius=1):
    r_vector = Vec3(radius,radius,radius)
    mc.setBlocks(hit.pos - r_vector, hit.pos + r_vector, block.AIR)

while True:
    if button.presses():
        control.hit()

    hits = mc.events.pollBlockHits()
    for hit in hits:
        dig(mc, hit)

    time.sleep(0.01)

