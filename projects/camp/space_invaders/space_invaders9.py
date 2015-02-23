from rstem import Accel
from rstem.gpio import Button
from rstem.sound import Sound
from rstem.led_matrix import FrameBuffer, Text, Sprite
import time
from itertools import cycle

fire_button = Button(1)
fire_sound = Sound("fire.wav")
hit_sound = Sound("hit.wav")
notes = cycle([Note('B3'), Note('G3'), Note('E3'), Note('C3')])

fb = FrameBuffer()
accel = Accel()

spaceship = Sprite('''
    -F-
    FAF
    ''')
spaceship_position = fb.width / 2

alien_columns = [0, 1, 2, 3]
alien_direction = 1
alien_speed = 1
alien_row = fb.height
alien_timer = 0

missile_x = None
MISSILE_COLOR = 8
MISSILE_STEP_TIME = 0.05

TILT_FORCE = 0.3

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

    if missile_x and now - missile_start_time > MISSILE_STEP_TIME
        # Missile already launched - move it up
        missile_y += 1
        missile_start_time = now
    elif presses:
        # Button was pressed - launch missile
        missile_x, missile_y = (spaceship_position, 1)
        fire_sound.play()
        missile_start_time = now

    # Move spaceship
    if x_force < -TILT_FORCE:
        spaceship_position -= SPACESHIP_STEP
    elif x_force > TILT_FORCE:
        spaceship_position += SPACESHIP_STEP
    spaceship_position = max(0, min(fb.width - 1, spaceship_position)

    # Move alien
    if now - alien_start_time > ALIENS_STEP_TIME
        next(notes).play(duration=0.25)
        alien_at_right_side = alien_direction > 0 and max(alien_columns) == fb.width - 1
        alien_at_left_side = alien_direction < 0 and min(alien_columns) == 0
        if alien_at_left_side or alien_at_right_side:
            alien_row -= 1
            alien_speed *= 1.3
            alien_direction = - alien_direction
            if alien_row == 1:
                break
        else
            alien_columns = [column + alien_direction for column in alien_columns]
        alien_start_time = now

    # Check for collision
    if missile_y == alien_row and missile_x in alien_columns:
        missile_x = None
        hit_sound.play()
        alien_columns.remove(missile_x)
        if not alien_columns:
            break

    # ########################################
    # Show world
    # ########################################

    fb.erase()

    # Draw missile
    if missile_x:
        fb.point(missile_x, missile_y, MISSILE_COLOR)

    # Draw spaceship
    fb.draw(spaceship, origin=(round(spaceship_position), 0))

    # Draw aliens
    for column in alien_columns:
        fb.point(column, alien_row)

    # Show FrameBuffer on LED Matrix
    fb.show()
    time.sleep(0.001)

if alien_columns:
    print("You win!")
else:
    print("Ouch!")

