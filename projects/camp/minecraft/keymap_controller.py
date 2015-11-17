from rstem.accel import Accel
from rstem.button import Button
from rstem.mcpi import minecraft, control
import time

control.show(hide_at_exit=True)

keymap = {
    Button(23) : control.left,
    Button(14) : control.right,
    Button(18) : control.forward,
    Button(15) : control.backward,
    }

accel = Accel()

while True:
    for button, action in keymap.items():
        if button.is_pressed():
            action()
        else:
            action(release=True)

    x, y, z = accel.forces()
    control.look(up=20*y, left=20*x)
    
    time.sleep(0.01)

