from rstem import led_matrix
import time

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.


# Scrolling the led matrix. ===============================================

# my_text_sprite is a variable that holds information on how to display your text.
my_text_sprite = led_matrix.LEDText("Hello World")


# A while loop that keeps looping forever
while True:  # by making the conditional True, the while loop will never break because True is always True!
   
   display_width = led_matrix.width()   # this is the number of LEDs wide the display is.
   
   text_width = my_text_sprite.width   # this is the number of LEDs wide our my_text_sprite is.
   
    # Set the x position to be originally all the way to the right of the screen, by using the text_width variable we made.
    x = text_width
    
    # Another while loop that keeps moving the text to the left.
    #   - When x is less then -text_width, our text will not be on the display anymore.
    #   - When this happens we want to stop this while loop and run through the outside while loop.
    while x > -text_width:   # when x is less then -text_width, our text will not be on the display anymore
        
        # Erase the previous drawn text
        led_matrix.erase()
        
        # Draw the text at this current x position
        led_matrix.sprite(text, (x, 0))
        
        # Show the text on the screen
        led_matrix.show()
        
        # Subtract 1 from x, so the next loop around moves the text one more to the left.
        x = x - 1
        
        # Hold for a second so we can see the text. (If we don't do this the text will move too quickly to see it.)
        time.sleep(1)
        
    
# Yay!! Now our text is continuously scrolling to the left.
# Try changing the number of seconds in the delay on step 15. (Or remove the line altogether!)

