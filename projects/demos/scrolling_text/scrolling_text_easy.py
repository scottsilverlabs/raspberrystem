from rstem import led_matrix
import time

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.


# Displaying text on the led matrix. ===============================================

# Draw the text "Hello World" on the LED matrix
# NOTE: this doesn't actually show the text on the display until we call led_matrix.show()
led_matrix.text("Hello World")

# To be able to see the text we need to tell the Raspberry Pi to show the drawn text on the led matrix.
led_matrix.show()


# Yay!! We can see the text on the led matrix!

# Try changing "Hello World" to something else and see what you get. :)  (Don't forget the " " )
