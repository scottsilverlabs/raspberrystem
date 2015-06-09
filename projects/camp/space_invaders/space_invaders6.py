from rstem.accel import Accel
from rstem.button import Button
from rstem.led_matrix import FrameBuffer
import time

fire_button = Button(25)

fb = FrameBuffer()
accel = Accel()

spaceship_position = fb.width / 2

aliens = [0, 1, 2, 3]
alien_row = fb.height - 1
alien_start_time = time.time()

ALIENS_STEP_TIME = 0.8

missile_x, missile_y = -1, -1

MISSILE_COLOR = 10
MISSILE_STEP_TIME = 0.1

TILT_FORCE = 0.1
SPACESHIP_STEP = 0.1

while True:
    # ########################################
    # Get inputs
    # ########################################
    presses = fire_button.presses()
    x_force, y_force, z_force = accel.forces()
    now = time.time()

    # ########################################
    # Change the World
    # ########################################

    if missile_x >= 0 and now - missile_start_time > MISSILE_STEP_TIME:
        # Missile already launched - move it up
        missile_y += 1
        if missile_y >= fb.height:
            missile_x, missile_y = -1, -1
        missile_start_time = now
    elif presses:
        # Button was pressed - launch missile
        missile_x, missile_y = (round(spaceship_position), 1)
        missile_start_time = now

    # Move spaceship
    if x_force > TILT_FORCE:
        spaceship_position -= SPACESHIP_STEP
    elif x_force < -TILT_FORCE:
        spaceship_position += SPACESHIP_STEP
    spaceship_position = max(0, min(fb.width - 1, spaceship_position))

    # Move alien
    if now - alien_start_time > ALIENS_STEP_TIME:
        aliens = [(column + 1) % fb.width for column in aliens]
        alien_start_time = now

    # Check for collision
    if missile_y == alien_row and missile_x in aliens:
        aliens.remove(missile_x)
        missile_x, missile_y = -1, -1
        if not aliens:
            break

    # ########################################
    # Show world
    # ########################################

    fb.erase()

    # Draw missile
    if missile_x >= 0:
        fb.point(missile_x, missile_y, MISSILE_COLOR)

    # Draw spaceship
    fb.point(round(spaceship_position), 0)

    # Draw aliens
    for column in aliens:
        fb.point(column, alien_row)

    # Show FrameBuffer on LED Matrix
    fb.show()
    time.sleep(0.001)

if aliens:
    print("Ouch!")
else:
    print("You win!")

