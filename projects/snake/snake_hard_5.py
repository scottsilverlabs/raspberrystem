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
from random import randint, choice  # used to create random numbers

# Set up LED matrix
led_matrix.init_grid()

# Set up buttons we will be using for our game
UP_button = button.UP()
DOWN_button = button.DOWN()
LEFT_button = button.LEFT()
RIGHT_button = button.RIGHT()


class Snake():
    def __init__(self):
        self.body = [(0, 0)]
        self.direction = "RIGHT"

    def draw(self):
        for point in self.body:
            led_matrix.point(point)

    def move(self, growing):
        # figure out the new point that will be added to the snake list
        pos_x, pos_y = self.body[0]
        if self.direction == "UP":
            if pos_y + 1 < led_matrix.height() - 1:
                new_point = (pos_x, pos_y + 1)
        elif self.direction == "DOWN":
            if pos_y > 0:
                new_point = (pos_x, pos_y - 1)
        elif self.direction == "LEFT":
            if pos_x > 0:
                new_point = (pos_x - 1, pos_y)
        elif self.direction == "RIGHT":
            if pos_x < led_matrix.width() - 1:
                new_point = (pos_x + 1, pos_y)
        else:
            raise ValueError("Bad Direction!!")  # show an error message if direction is not UP, DOWN, LEFT, or RIGHT
        # add new point to the head of snake
        if growing:
            self.body = [new_point] + self.body
        else:
            self.body = [new_point] + self.body[0:-1]


class Apple():
    def __init__(self, position):
        self.position = position

    def draw(self):
        led_matrix.point(self.position)


snake = Snake()  # create our snake for the game
apple = Apple((randint(0, led_matrix.width()), randint(0, led_matrix.height() - 1)))  # create an apple at a random location

while True:
    led_matrix.erase()
    snake.draw()
    apple.draw()
    led_matrix.show()
    snake.move(growing=False)  # move snake, but don't grow
    time.sleep(0.5)