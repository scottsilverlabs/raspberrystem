#!/usr/bin/env python3
import rstem
from rstem.gpio import Output
from random import randrange
import time

lights = [Output(4), Output(18), Output(14), Output(15)]

for light in lights:
    light.off()

play_order = []
failed = False
while not failed:
    play_order += [randrange(4)]

    # Play sequence
    for i in play_order:
        lights[i].on()
        time.sleep(0.4)
        lights[i].off()
        time.sleep(0.2)

    time.sleep(1.0)
