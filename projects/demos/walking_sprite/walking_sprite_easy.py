#!/usr/bin/env python


from rstem import led_matrix
import time
import os

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.


# Create sprite variables of the frames of a guy walking animation.
man1 = led_matrix.LEDSprite(os.path.abspath("man1.spr"))
man2 = led_matrix.LEDSprite(os.path.abspath("man2.spr"))
man3 = led_matrix.LEDSprite(os.path.abspath("man3.spr"))
man4 = led_matrix.LEDSprite(os.path.abspath("man4.spr"))
man5 = led_matrix.LEDSprite(os.path.abspath("man5.spr"))
man6 = led_matrix.LEDSprite(os.path.abspath("man6.spr"))
man7 = led_matrix.LEDSprite(os.path.abspath("man7.spr"))

# Put the sprite in a list to make it easy to loop through them.
frames = [man1, man2, man3, man4, man5, man6, man7]

# Create a while loop that loops forever.
while True:

    # Loop through each of the frames
    for current_sprite in frames:
        # Erase display to clear previous frame
        led_matrix.erase()
        
        # Draw current display
        led_matrix.sprite(current_sprite)
        
        # Show frame on screen
        led_matrix.show()
        
        # Delay to show the frame for a fraction of a second
        time.sleep(.25)
        
        
        
