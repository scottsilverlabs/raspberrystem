import sys
from rstem import led_matrix
import RPi.GPIO as GPIO
import random

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
        del self.body[-1]
        
    def collided_with_self(self):
        """Returns True if snake collided with itself."""
        if len(self.body) == 1:
            return False
        else:
            return self.body[0] is in self.body[1:]

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
        
class Field(object):
    """Keeps track off all pixels on the field"""
    def __init___(self, width, height):
        """Initialize field as given height and width"""
        self.points = set()
        # add all points
        for x in range(width):
            for y in range(height):
                self.points.add((x,y))
        self.size = width*height
        
    def new_apple(self, snake):
        """Adds a new apple in a random location in the field (removing old one)"""
        non_snake_points = self.points - set(snake.body)
        self.apple = random.sample(non_snake_points, 1)[0]
       
class State(object):
    RESET, PLAYING, WIN, LOSE, EXIT = range(5)
    
curr_state = RESET
snake = None
field = None
GROW_CYCLES = 20  # number of cycles to grow when eaten apple
score = 0

# initialize led matrix


# what to do during a button press
def button_handler(button):
    global curr_state
    if button == EXIT:
        led_matrix.shutdown_matrices()
        GPIO.cleanup()
        sys.exit(0)
    if curr_state is in [State.MOVING, State.GROWING]:
        if button == UP:
            snake.direction = Direction.UP
        elif button == DOWN:
            snake.direction = Direction.DOWN
        elif button == LEFT:
            snake.direction = Direction.LEFT
        elif button == RIGHT:
            snake.direction = Direction.RIGHT
    elif button == SELECT
        curr_state = State.RESET

# setup buttons  TODO: figure out correct port numbers
UP = 4
DOWN = 20
LEFT = 21
RIGHT = 22
SELECT = 23
EXIT = 18
GPIO.setmode(GPIO.BCM)
for button in [UP, DOWN, LEFT, RIGHT, SELECT, EXIT]:
    GPIO.setup(button, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=300)
    
while True:
    if curr_state == State.PLAYING:
        led_matrix.erase()
        move_success = snake.move()
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
        if not move_success or snake.collided_with_self():
            curr_state = State.LOSE
        if len(snake.body) >= field.size:
            curr_state = State.WIN
        if snake.pos == field.apple:
            field.new_apple()            # create new apple
            score += 1
            snake.growing = True         # snake starts growing
            snake.grow_clock = GROW_CYCLES
    elif curr_state == State.RESET:
        snake = Snake()
        field = Field(snake)
        score = 0
        led_matrix.erase()
        snake.draw()
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
    
