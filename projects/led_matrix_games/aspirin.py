from rstem import led_matrix, accel
import RPi.GPIO as GPIO

# set up led matrix
led_matrix.init_grid()

# set up buttons
A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22

# set up START and A buttons because those are the only buttons we will be using
GPIO.setmode(GPIO.BCM)
# TODO: set up buttons
#GPIO.setup(A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(START, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class Apple(object):
    # TODO: make the apple 2x2?
    def __init__(self, position):
        self.position = position
        
    def draw(self):
        led_matrix.point(*self.position)
        
class Striker(object):
    
    def __init__(self, start_pos, horizontal):
        self.position = start_pos     # starting position of the striker
        self.horizontal = horizontal  # true if striker is moving left and right, false if moving up and down
        
    def draw(self):
        led_matrix.point(*self.position)
        
class Player(object):
    
    def __init__(self, position=None, accel=False):
        # set position to be center of screen if position is not given
        if position is None:
            self.position = (led_matrix.width()/2, led_matrix.height()/2)
        else:
            self.position = position
        
        self.accel = accel  # True if controls are the accelometer, False if controls are buttons
        
    def move(self, direction):

# TODO:
#    - Figure out the best way to handle being able to use accelometer or controls elegantly
#        - do we want to use interupts for buttons like before.... makes accelometer seem
#            inconsistent.....
#        - or should we have the move function first check if accel or buttons and then poll
#            the directions.....
#        - or if accelometer do the whole angle thing... if keyboards a direction must be given...
#        - or have an update button that moves the player for accelometer all the time and does
#            nothing (or maybe there is some other stuff we have to do....)
        
        
        
        
        
        
        
        
        
