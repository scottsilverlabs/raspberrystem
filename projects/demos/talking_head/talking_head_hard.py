from rstem import led_matrix, speaker, button
import time
import os

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.

# TODO: Create a soundboard of different speeches by that are activated by pressing buttons....


# TODO: better (simpler to understand, yet elegant) way to do this?
# TODO: use less buttons?
# create a dictionary that matches the buttons (at ports 4, 17, 25, 24, 23, 18, 27, and 22) to the sound
soundboard = {
    button.Button(4) : speaker.Speech("Hello World"),
    button.Button(17) : speaker.Speech("How are you?"),
    button.Button(25) : speaker.Speech("RaspberrySTEM is super cool!"),
    button.Button(24) : speaker.Speech("The first 16 digits of pi is 3.141592653589793"),
    button.Button(23) : speaker.Speech("Always bring a banana to a party!"),
    button.Button(18) : speaker.Speech("I'm sorry Dave, I'm afraid I can't do that."),
    button.Button(27) : speaker.Speech("I am functioning within normal parameters."),
    button.Button(22) : speaker.Speech("EXTERMINATE!")
}

    
# Create sprite variables of a face with mouth open and closed from .spr files.
mouth_closed = led_matrix.LEDSprite(os.path.abspath("mouth_closed.spr"))
mouth_open = led_matrix.LEDSprite(os.path.abspath("mouth_open.spr"))

# create a while loop that will loop inifinitly by setting the conditional to True
while True:

    # originally set the speech to None because we haven't picked a speech to play yet
    my_speech = None
    
    # pick the first speech in which the button is pressed
    while my_speech is None:
        for button in soundboard:
            if button.is_pressed():
                my_speech = soundboard[button]
                break


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
        
    
    
    
    
