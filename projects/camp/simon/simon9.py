#!/usr/bin/env python3
import rstem
from rstem.button import Button
from rstem.gpio import Output
from rstem.sound import Note
from random import randrange
import time

buttons = [Button(27), Button(23), Button(24), Button(22)]
lights = [Output(4), Output(18), Output(14), Output(15)]
notes = [Note('A'), Note('B'), Note('C'), Note('D')]
you_failed_note = Note('E2')

for light in lights:
    light.off()

play_order = []
failed = False
while not failed:
    play_order += [randrange(4)]

    # Play sequence
    for i in play_order:
        lights[i].on()
        notes[i].play(0.4).wait()
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
        notes[button_pressed].play(duration=None)
        buttons[button_pressed].wait(press=False)
        time.sleep(0.2)
        lights[button_pressed].off()
        notes[button_pressed].stop()

    if not failed:
        time.sleep(1.0)

# Play error tone with pressed light (or all lights) on.
if button_pressed == None:
    for light in lights:
        light.on()
else:
    lights[button_pressed].on()
you_failed_note.play(1.5).wait()
for light in lights:
    light.off()
time.sleep(0.5)

# Play correct sequence fast
for i in play_order:
    lights[i].on()
    notes[i].play(0.1).wait()
    lights[i].off()
    time.sleep(0.05)
