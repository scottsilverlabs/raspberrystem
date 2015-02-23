from rstem import Accel
from rstem.led_matrix import FrameBuffer
import time

fb = FrameBuffer()
accel = Accel()

spaceship_position = fb.width / 2

alien_columns = [0, 1, 2, 3]
alien_row = fb.height

TILT_FORCE = 0.3

while True:
    # ########################################
    # Get inputs
    # ########################################
    x_force, y_force, z_force = accel.forces()
    now = time.time()

    # ########################################
    # Change the World
    # ########################################

    # Move spaceship
    if x_force < -TILT_FORCE:
        spaceship_position -= SPACESHIP_STEP
    elif x_force > TILT_FORCE:
        spaceship_position += SPACESHIP_STEP
    spaceship_position = max(0, min(fb.width - 1, spaceship_position)

    # Move alien
    if now - alien_start_time > ALIENS_STEP_TIME
        alien_columns = [(column + 1) % fb.width for column in alien_columns]
        alien_start_time = now

    # ########################################
    # Show world
    # ########################################

    fb.erase()

    # Draw spaceship
    fb.point(round(spaceship_position), 0)

    # Draw aliens
    for column in alien_columns:
        fb.point(column, alien_row)

    # Show FrameBuffer on LED Matrix
    fb.show()
    time.sleep(0.001)
