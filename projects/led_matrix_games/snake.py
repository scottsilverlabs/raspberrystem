import sys
from rstem import led_matrix
import RPi.GPIO as GPIO
import random
import time

class Direction(object):
    LEFT, RIGHT, UP, DOWN = range(4)

class Snake(object):
    """Keeps track of where the snake and its whole body is"""
    def __init__(self, pos=(3,3)):
        self.body = [pos]  # to start, snake is only one pixel long at pos
        self.direction = Direction.RIGHT  # start going right
        self.growing = False
        self.grow_clock = 0
        
    def head(self):
        return self.body[0]
        
    def tail(self):
        return self.body[-1]
        
    def remove_tail(self):
        if len(self.body) == 1:
            raise ValueError("Destroying snake body!")
        del self.body[-1]
        
    def collided_with_self(self):
        """Returns True if snake collided with itself."""
        if len(self.body) == 1:
            return False
        else:
            return self.body[0] in self.body[1:]
            
    def length(self):
        return len(snake.body)

    def move(self):
        """Moves the snake in the give direction (if it can).
        Snake will grow as it moves. Need to use remove_tail() afterwards if no growth wanted.
        Returns if it was able to succesfully move."""
        head_x, head_y = self.head()
        direction = snake.direction
        if direction == Direction.LEFT:
            if head_x == 0:
                return False
            new_point = (head_x - 1, head_y)
        elif direction == Direction.RIGHT:
            if head_x == led_matrix.width() - 1:
                return False
            new_point = (head_x + 1, head_y)
        elif direction == Direction.UP:
            if head_y == led_matrix.height() - 1:
                return False
            new_point = (head_x, head_y + 1)
        elif direction == Direction.DOWN:
            if head_y == 0:
                return False
            new_point = (head_x, head_y - 1)
        self.body = [new_point] + self.body  # add as new head
        return True
        
    def draw(self):
        for point in self.body:
            led_matrix.point(point)
        
class Field(object):
    """Keeps track off all pixels on the field"""
    def __init__(self, width, height):
        """Initialize field as given height and width"""
        self.points = set()
        # add all points
        for x in range(width):
            for y in range(height):
                self.points.add((x,y))
        self.size = width*height
        self.apple = None
        
    def new_apple(self, snake):
        """Adds a new apple in a random location in the field (removing old one)"""
        non_snake_points = self.points - set(snake.body)
        self.apple = random.sample(non_snake_points, 1)[0]
        
    def draw_apple(self):
        led_matrix.point(self.apple, color=9)
       
class State(object):
    RESET, PLAYING, WIN, LOSE, EXIT, IDLE = range(6)
    
curr_state = State.IDLE
snake = None
field = None
GROW_CYCLES = 0  # number of pixels - 1 to grow when eat apple
score = 0

# initialize led matrix
led_matrix.init_grid()

# setup buttons
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
SELECT = 22
START = 27
#A = 4
#B = 17

# wire them wrong temporaily so i can play it
LEFT = 24 # DOWN
UP = 23   # LEFT
DOWN = 18 # RIGHT
RIGHT = 25 # UP

# what to do during a button press
def button_handler(button):
    global curr_state
    if button == START:
        curr_state = State.EXIT
    if curr_state == State.PLAYING:
        if button == UP and (snake.length() == 1 or snake.direction != Direction.DOWN):
            snake.direction = Direction.UP
        elif button == DOWN and (snake.length() == 1 or snake.direction != Direction.UP):
            snake.direction = Direction.DOWN
        elif button == LEFT and (snake.length() == 1 or snake.direction != Direction.RIGHT):
            snake.direction = Direction.LEFT
        elif button == RIGHT and (snake.length() == 1 or snake.direction != Direction.LEFT):
            snake.direction = Direction.RIGHT
    elif button == SELECT:
        curr_state = State.RESET


GPIO.setmode(GPIO.BCM)
for button in [UP, DOWN, LEFT, RIGHT, START, SELECT]:
    GPIO.setup(button, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=300)
    
while True:
    if curr_state == State.PLAYING:
        led_matrix.erase()
        move_success = snake.move()
        if move_success:
            if snake.growing:
                if snake.grow_clock == 0:  # stop growing when clock hits zero
                    snake.growing = False
                else:
                    snake.grow_clock -= 1
            else:
                snake.remove_tail()
        snake.draw()
        field.draw_apple()
        led_matrix.show()
        
        # check if snake hit edge or its body
        if not move_success or snake.collided_with_self():
            curr_state = State.LOSE
            continue
            
        # check if snake has covered entire screen
        if len(snake.body) >= field.size:
            curr_state = State.WIN
            continue
            
        # if snake has gotten an apple, set up a new apple and start growing
        if snake.head() == field.apple:
            field.new_apple(snake)       # create new apple
            score += 1
            snake.growing = True         # snake starts growing
            snake.grow_clock = GROW_CYCLES
            
        time.sleep(.30)
        
    elif curr_state == State.IDLE:
        led_matrix.text("SNAKE")
        led_matrix.show()
    elif curr_state == State.RESET:
        snake = Snake()
        field = Field(led_matrix.width(), led_matrix.height())
        score = 0
        led_matrix.erase()
        snake.draw()
        field.new_apple(snake)
        field.draw_apple()
        led_matrix.show()
        curr_state = State.PLAYING
    elif curr_state == State.WIN:
        led_matrix.erase()
        led_matrix.text("WIN")  # TODO: scrolling text
        led_matrix.show()
    elif curr_state == State.LOSE:
        led_matrix.erase()
        led_matrix.text(str(score))
        led_matrix.show()
    elif curr_state == State.EXIT:
        led_matrix.shutdown_matrices()
        GPIO.cleanup()
        sys.exit(0)
        
        
        
