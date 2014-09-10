#!/usr/bin/env python

from rstem import led_matrix, button
import time
import os

led_matrix.init_grid(2,2)  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.

# Initialize a button at GPIO port 4 (the A button)
my_button = button.Button(4)

# Create sprite variables of the frames appended to the list
frames = []   # originally create an empty list
for i in range(1,8):  # a for loop that counts from 1 to 7
    # add mani.spr sprite to frame list, (where i is our current number 1-7)
    frames.append(led_matrix.LEDSprite(os.path.abspath("man" + str(i) + ".spr")))

# Create a while loop that loops forever.
while True:

    # Loop through each of the frames
    for current_sprite in frames:
        # Erase display to clear previous frame
        led_matrix.erase()
        
        # If the button is pressed we want to display the sprite jumping.
        if my_button.is_pressed():
            # draw the sprite up 2 pixels to simulate it jumping
            led_matrix.sprite(current_sprite, (0,2))
        else:
            # if not jumping draw the sprite at the origin
            led_matrix.sprite(current_sprite, (0,0))
        
        # Show sprite on screen
        led_matrix.show()
        
        # 8. Delay to show the frame for a fraction of a second
        time.sleep(.25)
        
        
        
