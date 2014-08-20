from rstem import led_matrix
import time

led_matrix.init_grid()  # This sets up the led matrix. It must be run before displaying anything.
led_matrix.erase()      # This clears the led matrix display incase anything is currently being displayed.


# Displaying multiple pieces of text in succession ===============================================

# create a while loop that loops infinitly
while True:

    # clear the display
    led_matrix.erase()
    
    # draw the first part of text
    led_matrix.text("Hello World", (0,0))
    
    # display the text
    led_matrix.show()
    
    # delay for a second so we can see the text
    time.sleep(1)
    
    # clear the display again so we can display the next part
    led_matrix.erase()
    
    # draw the next part of the text by setting the position 8 to the left
    led_matrix.text("Hello World", (-16,0))
    
    # display the text
    led_matrix.show()
    
    # delay for a second so we can see the text
    time.sleep(1)
    
    # it will now loop back to the beginning of the while loop and repeat
    
