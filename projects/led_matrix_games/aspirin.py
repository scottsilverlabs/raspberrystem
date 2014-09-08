from rstem import led_matrix, accel
import RPi.GPIO as GPIO
import random
import time
import sys

# notify of progress
print("P50")
sys.stdout.flush()

# set up led matrix
#led_matrix.init_grid(2,2)
led_matrix.init_matrices([(0,8),(8,8),(8,0),(0,0)])

# set up accelometer
accel.init(1)

# notify of progress
print("P60")
sys.stdout.flush()


# set up buttons
A = 4
B = 17
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
START = 27
SELECT = 22

# accelometer threshold
THRESHOLD = 3

        
class State(object):
    PLAYING, IDLE, SCORE, EXIT = range(4)
    
# starting variables
state = State.IDLE
field = None
title = led_matrix.LEDText("ASPIRIN - Press A to use accelometer or B to use buttons")

# notify of progress
print("P90")
sys.stdout.flush()

class Direction(object):
    LEFT, RIGHT, UP, DOWN = range(4)

class Apple(object):
    def __init__(self, position):
        self.position = position
        
    def draw(self):
        led_matrix.point(*self.position)
        
class Striker(object):
    
    def __init__(self, start_pos, direction):
        self.position = start_pos     # starting position of the striker
        self.direction = direction
        
    def draw(self):
        led_matrix.point(*self.position, color=3)
        
    def move(self):
        # check if the striker hit the wall and needs to bounce back
        if self.direction == Direction.LEFT and self.position[0] == 0:
            self.direction = Direction.RIGHT
        elif self.direction == Direction.RIGHT and self.position[0] == led_matrix.width()-1:
            self.direction = Direction.LEFT
        elif self.direction == Direction.DOWN and self.position[1] == 0:
            self.direction = Direction.UP
        elif self.direction == Direction.UP and self.position[1] == led_matrix.height()-1:
            self.direction = Direction.DOWN
            
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
            self.position = (int(led_matrix.width()/2), int(led_matrix.height()/2))
        else:
            self.position = position
        
        self.accel = accel  # True if controls are the accelometer, False if controls are buttons
        
    def draw(self):
        led_matrix.point(*self.position, color=8)
       
    def move(self, direction):
        if direction == Direction.UP:
            if self.position[1] < led_matrix.height()-1:
                self.position = (self.position[0], self.position[1]+1)
        elif direction == Direction.DOWN:
            if self.position[1] > 0:
                self.position = (self.position[0], self.position[1]-1)
        elif direction == Direction.LEFT:
            if self.position[0] > 0:
                self.position = (self.position[0]-1, self.position[1])
        elif direction == Direction.RIGHT:
            if self.position[0] < led_matrix.width()-1:
                self.position = (self.position[0]+1, self.position[1])
        else:
            raise ValueError("Invalid direction given.")
            
class Field(object):
    
    def __init__(self, player):
        self.player = player
        empty_strikers = set()
        # initialize empty strikers
        for x_pos in range(led_matrix.width()):
            empty_strikers.add(Striker((x_pos, 0), Direction.UP))
        for y_pos in range(led_matrix.height()):
            empty_strikers.add(Striker((0, y_pos), Direction.RIGHT))
        self.empty_strikers = empty_strikers   # strikers not used yet
        self.strikers = set()  # active strikers
        self.apple = None
        
    def draw(self):
        self.player.draw()
        self.apple.draw()
#        strikers = self.horizontal_strikers.union(self.vertical_strikers)
        for striker in self.strikers:
            striker.draw()
        
    def player_collided_with_apple(self):
        return self.player.position == self.apple.position
        
    def player_collided_with_striker(self):
#        strikers = self.horizontal_strikers.union(self.vertical_strikers)
        for striker in self.strikers:
            if self.player.position == striker.position:
                return True
        return False
        
    def new_apple(self):
        # set up list of x and y choices 
        x_pos = list(range(led_matrix.width()))
        y_pos = list(range(led_matrix.height()))
        # remove the position that player is currently in
        del x_pos[self.player.position[0]]
        del y_pos[self.player.position[1]]
        self.apple = Apple((random.choice(x_pos), random.choice(y_pos)))
        
    def add_striker(self):
        if len(self.empty_strikers) == 0:
            return False   # no more strikers to make, you win!!
        new_striker = random.choice(list(self.empty_strikers))
        self.strikers.add(new_striker)
        self.empty_strikers.remove(new_striker)
        return True
        

    
# set up buttons
GPIO.setmode(GPIO.BCM)

def button_handler(channel):
    global state
    global field
    if channel in [START, SELECT]:
        state = State.EXIT
    elif state in [State.IDLE, State.SCORE] and channel in [A, B]:
        # Reset field and player to start a new game
        player = Player(accel=(channel == A))
        field = None
        field = Field(player)
        field.new_apple()  # add the first apple
        state = State.PLAYING
#    elif state == State.PLAYING and (not field.player.accel) and channel in [UP, DOWN, LEFT, RIGHT]:
#        if channel == UP:
#            field.player.move(Direction.UP)
#        elif channel == DOWN:
#            field.player.move(Direction.DOWN)
#        elif channel == LEFT:
#            field.player.move(Direction.LEFT)
#        elif channel == RIGHT:
#            field.player.move(Direction.RIGHT)
    

for button in [UP, DOWN, LEFT, RIGHT, START, A, B, SELECT]:
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=100)
    
# notify of progress
print("P100")
sys.stdout.flush()

# notify menu we are ready for the led matrix
print("READY")
sys.stdout.flush()
    
# FSM =======
while True:
    if state == State.PLAYING:
        led_matrix.erase()
        
        # move player with accelometer, otherwise poll the buttons
        if field.player.accel:
            angles = accel.angles()
            #	"Simple" lowpass filter for velocity data
            x = angles[0]
            y = angles[1]
            
#            alpha = 0.2
#            velocity = 0.0
#            x_diff = velocity*alpha + (angles[0]*2*8/90)*(1 - alpha)
#            y_diff = velocity*alpha + (angles[1]*2*8/90)*(1 - alpha)
            if x > THRESHOLD:
                field.player.move(Direction.RIGHT)
            elif x < -THRESHOLD:
                field.player.move(Direction.LEFT)
            if y > THRESHOLD:
                field.player.move(Direction.DOWN)
            elif y < -THRESHOLD:
                field.player.move(Direction.UP)
        else:
            if GPIO.input(UP) == 0:
                field.player.move(Direction.UP)
            if GPIO.input(DOWN) == 0:
                field.player.move(Direction.DOWN)
            if GPIO.input(LEFT) == 0:
                field.player.move(Direction.LEFT)
            if GPIO.input(RIGHT) == 0:
                field.player.move(Direction.RIGHT)
                
        # move the strikers
        for striker in field.strikers:
            striker.move()
        	
    	  
	    # draw all the objects on the field      
        field.draw()
        led_matrix.show()
        
        # check for collisions
        if field.player_collided_with_striker():
            state = State.SCORE
        elif field.player_collided_with_apple():
            field.new_apple()
            ret = field.add_striker()
            if ret == False:
                state = State.SCORE
        
        time.sleep(.1)
        
        
    elif state == State.IDLE:
        x = led_matrix.width()
        while x > -title.width:
            # break if state has changed, (don't wait for scroll to finish)
            if state != State.IDLE:
                break
            led_matrix.erase()
            led_matrix.sprite(title, (x, led_matrix.height()/2 - (title.height/2)))
            led_matrix.show()
            x -= 1
            time.sleep(.05)
            
    elif state == State.SCORE:
        led_matrix.erase()
        led_matrix.text(str(len(field.strikers)))
#        led_matrix.text(str(len(field.horizontal_strikers) + len(field.vertical_strikers)))
        led_matrix.show()
        
    elif state == State.EXIT:
        GPIO.cleanup()
        led_matrix.cleanup()
        sys.exit(0)
    else:
        raise ValueError("Invalid State")
        
        
        
        
        
        
        
        
        
