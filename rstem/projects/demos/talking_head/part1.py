from rstem import led_matrix, speaker
import time
import os

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.

# 1. Create sprite variables of a face with mouth open and closed from .spr files.
mouth_closed = led_matrix.LEDSprite(os.path.abspath("mouth_closed.spr"))
mouth_open = led_matrix.LEDSprite(os.path.abspath("mouth_open.spr"))


# 2. Make the RaspberryPi say "Hello World"
speaker.say("Hello World")

# 3. Create a while loop that keeps looping until the Raspberry Pi has stopped talking.
while speaker.is_talking():
    # 4. Clear the led matrix
    led_matrix.erase()
    
    # 5. Draw the face with its mouth open
    led_matrix.sprite(mouth_open)
    
    # 6. Show the new face on the display and add a delay
    led_matrix.show()
    time.sleep(.1)
    
    # 7. Clear the led matrix of the previous face
    led_matrix.erase()
    
    # 8. Draw the face with its mouth closed
    led_matrix.sprite(mouth_closed)
    
    #9. Show the new face on the display and add a delay
    led_matrix.show()
    time.sleep(.1)
    
    
    
    
    
