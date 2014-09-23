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

# Set up LED matrix
led_matrix.init_grid()

# Set up buttons we will be using for our game
UP_button = button.UP()
DOWN_button = button.DOWN()
LEFT_button = button.LEFT()
RIGHT_button = button.RIGHT()

# Create a variable that defines the location of the snake
snake_position = (0,0)   # start the snake at the bottom left corner

# Create a while loop that is continuously displaying the snake
while True:
    led_matrix.erase()  # erase what was previously on the LED matrix
    led_matrix.point(snake_position)   # draw the snake at snake_position
    led_matrix.show()   # show the snake on the LED matrix