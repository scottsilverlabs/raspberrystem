#This is the second project in the "Space invaders" series.
#This project adds missles to the game when the player
#presses the button.

#Imports, need sys for exit function
from rstem import led_matrix
from rstem import accel
import RPi.GPIO as GPIO
import time

#Initialize matrix, accelerometer, and GPIO, the matrix layout and accelerometer channel may changes from user to user
led_matrix.init_grid(2)
accel.init(1)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#Game entity data
player_pos = [7, 0]
missles = []

#Game timing data, missles get updated and therefore move roughly sixty times faster than enemies initialy
game_tick = 0
game_tick_max = 64
enemy_tick = 60
start_time = time.time()

#Function to add missle at the players position to set of current missles
def fire_missle(channel):
    missles.append(Missle([int(round(player_pos[0])), int(round(player_pos[1]))],[0, 1]))

#Call fire_missle when fire button is pressed
GPIO.add_event_detect(4, GPIO.FALLING, callback=fire_missle, bouncetime = 300)

#Useful clamp function to make sure the data passed to point is on the matrix
def clamp(x):
    return max(0, min(x, 15))

#Missle keeps track of its current position and current direction
class Missle:
    
    def __init__(self, position, direction):
        self.pos = position
        self.dir = direction

#   Move missle on missle update tick
    def update(self):
        self.pos[0] = self.pos[0] + self.dir[0]
        self.pos[1] = self.pos[1] + self.dir[1]
        if self.pos[1] > 15 or self.pos[1] < 0 or self.pos[0] < 0 or self.pos[1] > 15:
            missles.remove(self)
try:
#   Start game
    while True:

#       Clear previous framebuffer    
        led_matrix.fill(0)

#       Update and redraw missles
        for m in missles:
            m.update()    
            led_matrix.point(m.pos[0], m.pos[1])

#       Get angles from accelerometer
        data = accel.angles()

#       Generate smooth movement data using IIR filter, and make a 1/4 turn move
#       the player to the edge of the screen
        player_pos[0] = player_pos[0] + (clamp(-data[0]*8*4/90 + 7) - player_pos[0])*0.1
    
#       Draw player
        led_matrix.point(int(round(player_pos[0])), int(round(player_pos[1])))

#       Show framebuffer
        led_matrix.show()

#       Delay one game tick, in this case 1ms
        time.sleep(0.001)

#Stop if player hits Ctrl-C
except KeyboardInterrupt:
        pass

#Clean everything up
finally:
        GPIO.cleanup()
        led_matrix.cleanup()
