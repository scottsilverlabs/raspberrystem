from rstem.led_matrix import FrameBuffer, Sprite
from rstem.gpio import Output
import time
from random import random

fb = FrameBuffer([(0,0,90)])

outs = [ Output(17), Output(27), Output(22), Output(23), Output(4), Output(14), Output(15), Output(18), ]

with open('scroller1.spr') as f:
    s1 = Sprite(f.read())
s1_width = s1.width
s1 += s1

with open('scroller2.spr') as f:
    s2 = Sprite(f.read())
s2_width = s2.width
s2 += s2

i = 0
i1 = 0
i2 = 0
x = 4
while True:
    fb.erase()
    fb.draw(s1, (-i1,0))
    fb.draw(s2, (-i2,0))
    fb.show()
    time.sleep(0.01)
    if i1 == s1_width:
        i1 = 0
    elif i % 15 == 0:
        i1 += 1
    if i2 == s2_width:
        i2 = 0
    elif i % 4 == 0:
        i2 += 1
    i += 1


    if i % 12 == 0:
        r = random()
        if r < 0.3:
            x -= 1
        elif r > 0.7:
            x += 1
        x = max(1, min(7,x))
    for j in range(8):
        if j < x:
            outs[j].on()
        else:
            outs[j].off()

