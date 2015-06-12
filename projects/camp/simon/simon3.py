#!/usr/bin/env python3
import rstem
from rstem.gpio import Output
import time

lights = [Output(4), Output(27), Output(17), Output(25)]

for light in lights:
    light.off()

lights.on()
time.sleep(1)
lights.off()
