#!/usr/bin/env python3
from rstem.button import Button
from rstem.sound import Note

buttons = [Button(22), Button(23), Button(24), Button(27)]
notes = [Note('A'), Note('B'), Note('C'), Note('D')]

while True:
    for button, note in zip(buttons, notes):
        if button.is_pressed():
            if not note.is_playing():
                note.play(duration=None)
        else:
            note.stop()
