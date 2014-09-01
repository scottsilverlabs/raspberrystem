from rstem import led_matrix, speaker, button
import time
import os

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.

# TODO: Create a soundboard of different speeches by that are activated by pressing buttons....

# setup the button port numbers
A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22

# create a dictionary that matches the buttons to the sound
soundboard = {
    button.Button(A) : speaker.Speech("Hello World"),
    button.Button(B) : speaker.Speech("How are you?"),
    button.Button(UP) : speaker.Speech("RaspberrySTEM is super cool!"),
    button.Button(DOWN) : speaker.Speech("The first 16 digits of pi is 3.141592653589793"),
    button.Button(LEFT) : speaker.Speech("Always bring a banana to a party!"),
    button.Button(RIGHT) : speaker.Speech("I'm sorry Dave, I'm afraid I can't do that."),
    button.Button(START) : speaker.Speech("I am functioning within normal parameters."),
    button.Button(SELECT) : speaker.Speech("EXTERMINATE!")
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

    # TODO: us say instead of speech???
    
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
        
    
    
    
    
