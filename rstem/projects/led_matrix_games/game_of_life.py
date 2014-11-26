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

import sys
import os
from rstem import led_matrix, button
import random
import time

# notify of progress
print("P50")
sys.stdout.flush()

# initialize led matrix
#led_matrix.init_grid(2,2)
led_matrix.init_matrices([(0,8),(8,8),(8,0),(0,0)])


# set up buttons
A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22

# setup exit and restart button
exit_button = button.Button(START)
restart_button = button.Button(A)

# notify of progress
print("P60")
sys.stdout.flush()

# initialize variables
num_rows, num_cols, curr_gen, next_gen = (None, None, None, None)
    
    
def get_num_neighbors(curr_gen, x, y):
    """Returns the number of (alive) neighbors of given pixel"""
    count = 0
    for j in range(y-1, y+2):
        for i in range(x-1, x+2):
            if not(i == x and j == y):  # don't count itself
                if i >= 0 and i < led_matrix.width() and j >= 0 and j < led_matrix.height():
                    if curr_gen[j][i] == 0xF:
                        count += 1
    return count
    
def next_generation():
    """Creates next generation using Conway's Game of Life rules:
    http://en.wikipedia.org/wiki/Conway's_Game_of_Life
    """
    global next_gen
    global curr_gen
    for y in range(0,num_rows):
        for x in range(0,num_cols):
            num_neighbors = get_num_neighbors(curr_gen, x, y)
            if curr_gen[y][x] == 0xF and num_neighbors < 2:
                next_gen[y][x] = 0  # pixel died off, not enough neighbors
            elif curr_gen[y][x] == 0xF and num_neighbors > 3:
                next_gen[y][x] = 0  # pixel died off, too many neighbors
            elif curr_gen[y][x] == 0 and num_neighbors == 3:
                next_gen[y][x] = 0xF  # birth of a new pixel
            else:
                next_gen[y][x] = curr_gen[y][x]
    curr_gen, next_gen = next_gen, curr_gen  # swap lists
    
def random_grid(width, height):
    """Creates a grid of random dead and alive pixels."""
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            random_num = random.randint(0,3)
            if random_num == 0:  # make alive pixels less common
                row.append(0xF)  # add an alive pixel
            else:
                row.append(0x0)  # add a dead pixel
        grid.append(row)
    return grid
    
def draw_grid():
    """Draws the current generation to led_matrix."""
    for y in range(num_rows):
        for x in range(num_cols):
            led_matrix.point(x, y, curr_gen[y][x])
                
# whole game loop
while True:            
    # variables
    num_rows = led_matrix.height()
    num_cols = led_matrix.width()

    # notify of progress
    print("P80")
    sys.stdout.flush()
    curr_gen = random_grid(num_cols, num_rows)

    # notify of progress
    print("P90")
    sys.stdout.flush()
    next_gen = [[0 for i in range(num_cols)] for j in range(num_rows)]
    # TODO allow sprite input instead of random grid?

    # notify menu we are ready for the led matrix
    print("READY")
    sys.stdout.flush()

    # single game loop
    while True:
        if exit_button.is_pressed():
            # clean up stuff and exit the program
            button.cleanup()
            led_matrix.cleanup()
            sys.exit(0)
        elif restart_button.is_pressed():
            break  # break out of this inner loop (lets us restart generations)
        else:
            led_matrix.erase()   # clear the display
            draw_grid()          # draw the current generation
            led_matrix.show()    # show on display
            next_generation()    # update generation to next generation
    
