from rstem import led_matrix
import time

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.


# Displaying moved text on the led matrix. ===============================================

my_text_sprite = led_matrix.LEDText("Hello World")
# Note: my_text_sprite is a variable that holds information on how to display your text.


# 4. Now, lets draw the my_text_sprite onto the display, but this time display the text at a different (x,y) position
led_matrix.sprite(my_text_sprite, (-4,0))
# Note: We can display the text at different locations by giving an (x,y) coordinate. 
#   - This (x,y) coordinate is the location of the bottom left of the text.
#   - If no position is given (like we did in part 1), the computer assumes you want the position to be (0,0)
#   - So if we want to move the text to the left we give an x value that is less than 0. Like (-4,0)

led_matrix.show()


# Yay!! Now we can see that the text has been moved to the left by 4 pixels.
# Try different (x,y) coordinates and see what you get.
