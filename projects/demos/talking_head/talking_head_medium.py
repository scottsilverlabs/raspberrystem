from rstem import led_matrix, speaker
import time
import os

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.

# Create sprite variables of a face with mouth open and closed from .spr files.
mouth_closed = led_matrix.LEDSprite(os.path.abspath("mouth_closed.spr"))
mouth_open = led_matrix.LEDSprite(os.path.abspath("mouth_open.spr"))

# Create a speech object of "Hello World"
my_speech = speaker.Speech("Hello World")

# Play my_speech
my_speech.play()

# Create a while loop that keeps looping until the Raspberry Pi has stopped talking.
while my_speech.is_playing():

    # Clear the led matrix
    led_matrix.erase()
    
    # Draw the face with its mouth open
    led_matrix.sprite(mouth_open)
    
    # Show the new face on the display and add a delay
    led_matrix.show()
    time.sleep(.1)
    
    # Clear the led matrix of the previous face
    led_matrix.erase()
    
    # Draw the face with its mouth closed
    led_matrix.sprite(mouth_closed)
    
    # Show the new face on the display and add a delay
    led_matrix.show()
    time.sleep(.1)
    
    
    
    
    
