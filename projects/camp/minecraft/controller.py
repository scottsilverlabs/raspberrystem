from rstem.accel import Accel
from rstem.button import Button
from rstem.mcpi import minecraft, control
import time

control.show(hide_at_exit=True)

left = Button(23)
right = Button(14)
up = Button(18)
down = Button(15)

accel = Accel()

while True:
    if left.is_pressed():
        control.left()
    else:
        control.left(release=True)
    if right.is_pressed():
        control.right()
    else:
        control.right(release=True)
    if up.is_pressed():
        control.forward()
    else:
        control.forward(release=True)
    if down.is_pressed():
        control.backward()
    else:
        control.backward(release=True)

    x, y, z = accel.forces()
    control.look(up=20*y, left=20*x)
    
    time.sleep(0.01)

