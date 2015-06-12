#!/usr/bin/env python3
import rstem
from rstem.button import Button
from rstem.gpio import Output
from random import randrange
import time

buttons = [Button(27), Button(23), Button(24), Button(22)]
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

    # Wait for user to repeat
    for i in play_order:
        button_pressed = Button.wait_many(buttons, timeout=3)

        if button_pressed != i:
            failed = True
            break

        # Light and play while button is pressed.
        lights[button_pressed].on()
        buttons[button_pressed].wait(press=False)
        time.sleep(0.2)
        lights[button_pressed].off()

    if not failed:
        time.sleep(1.0)
