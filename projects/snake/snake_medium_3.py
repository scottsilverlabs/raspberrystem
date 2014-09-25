#!/usr/bin/env python3

#
# Copyright (c) 2014, Scott Silver Labs, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# import cells we will be using
from rstem import led_matrix, button
import time
from random import randint  # used to create random numbers

# Set up LED matrix
led_matrix.init_grid()

# Set up buttons we will be using for our game
UP_button = button.UP()
DOWN_button = button.DOWN()
LEFT_button = button.LEFT()
RIGHT_button = button.RIGHT()

# Create a list that defines all the points of the snake's body
snake = [(0, 0)]   # start the snake at the bottom left corner

# Create a position variable for the apple
apple_position = (randint(0, led_matrix.width() - 1), randint(0, led_matrix.height() - 1))

# Create a variable that defines the snake_position the snake is moving
direction = "RIGHT"

# Create a while loop that is continuously displaying the snake
while True:
    led_matrix.erase()  # erase what was previously on the LED matrix

    # change the direction when the usr presses a button
    if UP_button.is_pressed():
        direction = "UP"
    if DOWN_button.is_pressed():
        direction = "DOWN"
    if LEFT_button.is_pressed():
        direction = "LEFT"
    if RIGHT_button.is_pressed():
        direction = "RIGHT"

    # figure out the new point that will be added to the snake list
    pos_x, pos_y = position
    if direction == "UP":
        if pos_y + 1 < led_matrix.height() - 1:
            new_point = (pos_x, pos_y + 1)
    elif direction == "DOWN":
        if pos_y > 0:
            new_point = (pos_x, pos_y - 1)
    elif direction == "LEFT":
        if pos_x > 0:
            new_point = (pos_x - 1, pos_y)
    elif direction == "RIGHT":
        if pos_x < led_matrix.width() - 1:
            new_point = (pos_x + 1, pos_y)
    else:
        raise ValueError("Bad Direction!!")  # show an error message if direction is not UP, DOWN, LEFT, or RIGHT
    # add the new point to the beginning of the snake and remove the tail at the same time
    snake = [new_point] + snake[0:-1]

    # check if the snake has collided with the apple
    if apple_position == snake[0]:
        # pick a new position for the apple
        apple_position = (randint(0, led_matrix.width() - 1), randint(0, led_matrix.height() - 1))

    # draw the snake list
    for point in snake:
        led_matrix.point(point)

    led_matrix.point(apple_position)   # draw the apple at apple_position

    led_matrix.show()   # show the snake on the LED matrix

    # delay the time for 0.5 seconds
    time.sleep(0.5)