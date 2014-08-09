from rstem import led_matrix, button
import time
import os

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.

# Create sprite variables of the frames appended to the list
frames = []   # originally create an empty list
for i in range(1,8):  # a for loop that counts from 1 to 7
    # add mani.spr sprite to frame list, (where i is our current number 1-7)
    frames.append(led_matrix.LEDSprite(os.path.abspath("man" + str(i) + ".spr")))
    
# Create a variable that indicates if the sprite is moving left or right.
moving_right = True  # if True it is moving right, if False it is moving left

# Create an x variable that indicates the current x position the sprite is on the display
x = 0  # initially we want our x value to be 0

# Create a while loop that loops forever.
while True:

    # Loop through each of the frames
    for sprite in frames:
        # Erase display to clear previous sprite
        led_matrix.erase()
        
        if moving_right:
            # show the sprite as normal (facing right)
            led_matrix.sprite(sprite, (x,0))
        else:
            # show the sprite flipped vertical (faceing left)
            led_matrix.sprite(sprite.flipped_vertical(), (x,0))
            
        # Show sprite on screen
        led_matrix.show()
        
        # Update the x value to move it left or right
        if moving_right:
            x = x + 1  # increase the x if we are moving right
        else:
            x = x - 1  # decrease the x if we are moving left
        
        # if the sprite has hit the right side of the display and we are moving right, the sprite should switch to moving left
        if moving_right and x > (led_matrix.width() - sprite.width):
            moving_right = False  # switch to moving left
        # else if the sprite has hit the left side of the display and is moving left, the sprite should switch to moving right
        elif not moving_right and x == 0:
            moving_right = True
        
        # Delay to show the frame for a fraction of a second
        time.sleep(.2)
        
        
        
