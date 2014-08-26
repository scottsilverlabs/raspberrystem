from rstem import led_matrix, button
import time
import sys

# initialize led matrix
#led_matrix.init_grid()
led_matrix.init_matrices([(0,8),(8,8),(8,0),(0,0)])


start_button = button.Button(button.START)

while True:
    if start_button.is_pressed():
        button.cleanup()
        led_matrix.cleanup()
        sys.exit(0)
        
    hour = time.strftime("%I", time.localtime())
    hour = led_matrix.LEDText(hour)
    minute = time.strftime("%M", time.localtime())
    minute = led_matrix.LEDText(minute)
    
    led_matrix.erase()
    led_matrix.text(hour)
    led_matrix.text(minute, (hour.width + 2, 0))
    led_matrix.show()
