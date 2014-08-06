from rstem import led_matrix
import time

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.


# Displaying text on the led matrix. ===============================================


# 1. Convert your text into an LED sprite we can display on the led matrix.
my_text_sprite = led_matrix.LEDText("Hello World")
# Note: my_text_sprite is a variable that holds information on how to display your text.


# 2. Now, lets draw the my_text_sprite onto the display.
led_matrix.sprite(my_text_sprite)


# 3. To be able to see the text we need to tell the Raspberry Pi to show the drawn text on the led matrix.
led_matrix.show()


# Yay!! We can see the text on the led matrix!

# Try changing "Hello World" to something else and see what you get. :)  (Don't forget the " " )
