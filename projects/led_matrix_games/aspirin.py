from rstem import led_matrix, accel
import RPi.GPIO as GPIO
import random
import time

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


class Direction(object):
    LEFT, RIGHT, UP, DOWN = range(4)

class Apple(object):
    # TODO: make the apple 2x2?
    def __init__(self, position):
        self.position = position
        
    def draw(self):
        led_matrix.point(*self.position)
        
class Striker(object):
    
    def __init__(self, start_pos, direction):
        self.position = start_pos     # starting position of the striker
        self.direction = direction
        
    def draw(self):
        led_matrix.point(*self.position, color=5)
        
    def move(self):
        # check if the striker hit the wall and needs to bounce back
        if self.direction == Direction.LEFT and self.position[0] == 0:
            self.direction == Direction.RIGHT
        elif self.direction == Direction.RIGHT and self.position[0] == led_matrix.width()-1:
            self.direction == Direction.LEFT
        elif self.direction == Direction.DOWN and self.position[1] == 0:
            self.direction == Direction.UP
        elif self.direction == Direction.UP and self.position[1] == led_matrix.height()-1:
            self.direction == Direction.DOWN
            
        if self.direction == Direction.LEFT:
            self.position = (self.position[0]-1, self.position[1])
        elif self.direction == Direction.RIGHT:
            self.position = (self.position[0]+1, self.position[1])
        elif self.direction == Direction.DOWN:
            self.position = (self.position[0], self.position[1]-1)
        elif self.direction == Direction.UP:
            self.position = (self.position[0], self.position[1]+1)
        
class Player(object):
    
    def __init__(self, position=None, accel=False):
        # set position to be center of screen if position is not given
        if position is None:
            self.position = (led_matrix.width()/2, led_matrix.height()/2)
        else:
            self.position = position
        
        self.accel = accel  # True if controls are the accelometer, False if controls are buttons
        
    def draw(self):
        led_matrix.point(*self.position)
       
    # TODO: make this more elegant 
    def move(self, direction):
        if direction == Direction.UP:
            if self.position[1] != led_matrix.height()-1:
                self.position = (self.position[0], self.position[1]+1)
        elif direction == Direction.DOWN:
            if self.position[1] != 0:
                self.position = (self.position[0], self.position[1]-1)
        elif direction == Direction.LEFT:
            if self.position[0] != 0:
                self.position = (self.position[0]-1, self.position[1])
        elif direction == Direction.RIGHT:
            if self.position[0] != led_matrix.width()-1:
                self.position == (self.position[0]+1, self.position[1])
        else:
            raise ValueError("Invalid direction given.")
            
class Field(object):
    
    def __init__(self, player):
        self.player = player
        self.horizontal_strikers = set()
        self.vertical_strikers = set()
        self.apple = None
        
    def draw(self):
        self.player.draw()
        self.apple.draw()
        strikers = self.horizontal_strikers.union(self.vertical_strikers)
        for striker in strikers:
            striker.draw()
        
    def player_collided_with_apple(self):
        return self.player.position == self.apple.position
        
    def player_collided_with_striker(self):
        strikers = self.horizontal_strikers.union(self.vertical_strikers)
        for striker in strikers:
            if self.player.position == striker.position:
                return True
        return False
        
    def new_apple(self):
        # set up list of x and y choices 
        x_pos = range(led_matrix.width())
        y_pos = range(led_matrix.height())
        # remove the position that player is currently in
        del x_pos[player.position[0]]
        del y_pos[player.position[1]]
        self.apple = Apple((random.choice(x_pos), random.choice(y_pos))
        
    def add_striker(self):
        horizontal = None
        # get all possible combinations of horizontal and vertical strikers
        x_pos = set(range(led_matrix.width())) - set([striker.position[0] for striker in self.vertical_strikers])
        y_pos = set(range(led_matrix.height())) - set([striker.position[1] for striker in self.horizontal_strikers])
        if len(x_pos) == 0:
            if len(y_pos) == 0:
                return False   # both sets are empty, the entire field is filled, you win!!
            horizontal = True
        elif len(y_pos) == 0:
            horizontal = False
        else:
            horizontal = random.choice([True, False])    
    
        if horizontal:
            direction = random.choice([Direction.LEFT, Direction.RIGHT])
            start_position = (0, random.choice(list(y_pos))
            self.horizontal_strikers.add(start_position, direction)
        else:
            direction = random.choice([Direction.UP, Direction.DOWN])
            start_position = (random.choice(list(x_pos)), 0)
            self.vertical_strikers.add(start_position, direction)
                
        return True
        
        
class State(object):
    PLAYING, IDLE, SCORE, EXIT = range(4)
    
# starting variables
state = State.IDLE
player = None
field = None
    
# set up buttons
GPIO.setmode(GPIO.BCM)

def button_handler(channel):
    global state
    if channel == START:
        state.EXIT
    elif state in [State.IDLE, State.SCORE] and channel in [A, B]:
        # Reset field and player to start a new game
        player = Player(accel=(channel == A))
        field = None
        field = Field()
        field.new_apple()  # add the first apple
        state = state.PLAYING
    elif state == State.PLAYING and (not player.accel) and channel in [UP, DOWN, LEFT, RIGHT]:
        if channel == UP:
            player.move(Direction.UP)
        elif channel == DOWN:
            player.move(Direction.DOWN)
        elif channel == LEFT:
            player.move(Direction.LEFT)
        elif channel == RIGHT:
            player.move(Direction.RIGHT)
    

for button in [UP, DOWN, LEFT, RIGHT, START, A, B]:
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(button, callback=button_handler, bouncetime=300)
    
# FSM =======
while True:
    if state == state.PLAYING:
        # TODO when i get home
        # DO THIS ONE THEN TEST IT OUT!! DRINK LOTS OF WATER>>>> PAST SELF would like this VERY MUCH
        led_matrix.erase()
        
        # move player with accelometer, otherwise button_handler takes care of moving player
        if player.accel:
            # TODO: debug this
            angles = accel.angles()
            #	"Simple" lowpass filter for velocity data
            alpha = 0.1
            velocity = 0.0
            x_diff = velocity*alpha + (angles[0]*2*8/90)*(1 - alpha)
        	y_diff = velocity*alpha + (angles[1]*2*8/90)*(1 - alpha)
        	if x_diff > 0:
        	    player.move(Direction.RIGHT)
	        elif x_diff < 0:
	            player.move(Direction.LEFT)
            if y_diff > 0:
                player.move(Direction.UP)
            elif y_diff < 0:
                player.move(Direction.DOWN)
        	
#        	x_direction = Direction.RIGHT if x_diff > 0 else Direction.LEFT
#        	y_direction = Direction.UP if y_diff > 0 else Direction.DOWN
#        	
#        	# move player certain number of times vertically and horizontally
#        	for _ in range(int(abs(x_diff))):
#        	    player.move(x_direction)
#    	    for _ in range(int(abs(y_diff))):
#    	        player.move(y_direction)
    	  
	    # draw all the objects on the field      
        field.draw()
        
        # check for collisions
        if field.player_collided_with_striker():
            state = state.SCORE
        elif field.player_collided_with_apple():
            field.new_apple()
            field.add_striker()
        
        time.sleep(.5)
        	
        
    elif state == state.IDLE:
        # TODO: check speed on this
        text = led_matrix.LEDText("ASPIRIN - Press A to use accelometer or B to use buttons")
        x = led_matrix.width()s
        while x > -text.width:
            # break if state has changed, (don't wait for scroll to finish)
            if state != state.IDLE:
                break
            led_matrix.erase()
            led_matrix.sprite(text, (x, led_matrix.height()/2 - (text.height/2)))
            led_matrix.show()
            x -= 1
            # TODO: delay needed?
            
    elif state == state.SCORE:
        led_matrix.erase()
        led_matrix.text(len(field.horizontal_strikers) + len(field.vertical_strikers))
        led_matrix.show()
        
    elif state == state.EXIT:
        GPIO.cleanup()
        led_matrix.cleanup()
        sys.exit(0)
    else:
        raise ValueError("Invalid State")



# TODO: set up buttons
#GPIO.setup(A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(START, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        
# TODO:
#    - Figure out the best way to handle being able to use accelometer or controls elegantly
#        - do we want to use interupts for buttons like before.... makes accelometer seem
#            inconsistent.....
#        - or should we have the move function first check if accel or buttons and then poll
#            the directions.....
#        - or if accelometer do the whole angle thing... if keyboards a direction must be given...
#        - or have an update button that moves the player for accelometer all the time and does
#            nothing (or maybe there is some other stuff we have to do....)
        
        
        
        
        
        
        
        
        
