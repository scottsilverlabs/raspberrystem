import time
import os
import random
import sys
from rstem import led_matrix
import RPi.GPIO as GPIO

# initialization
led_matrix.init_grid(angle=90)  # make longwise
GPIO.setmode(GPIO.BCM)

#TODO: combine peice and shape together having the sprites already generated
# for each type.... have functions that iterate through to describe what 
# points are valid by comparing "-" vs (another color)

# game variables
score = 0
BLINKING_TIME = 15 # number of cycles to blink full lines

class Stack(object);
    """Represents the stack of rested tetris pieces"""
    def __init__(self):
        self.points = [] # 2D list that represents stacks's color for each point
        
    def height(self):
        return len(self.points)
        
    def add(self, piece):
        """Adds given piece to the stack
        @param piece: piece to add to stack, should be touching current stack
        @type piece: L{Piece}
        """
        for y_offset, line in enumerate(reversed(piece.sprite.bitmap)): # iterate going up
            # check if we need to add a new line to the stack
            # TODO: change to a while loop?
            if piece.pos[1] + y_offset > (len(stack.points) - 1):
                assert piece.pos[1] + y_offset == len(stack.points)
                # add a new line to stack and fill with transparent pixels (this is new top of stack)
                self.points.append([16 for i in range(led_matrix.width())])
            for x_offset, pixel in enumerate(line):
                # add piece if not transparent
                if pixel != 16:
                    stack[piece.pos[1] + y_offset][piece.pos[0] + x_offset] = pixel
                    
    def draw(self, blinking_off=False):
        """Draws stack on led display
        @param blinking_off: If set, it will display full lines as a line of all color == 0.
            Useful for blinking full lines.
        @type blinking_off: boolean
        """
        assert self is not None
        for y, line in enumerate(self.points):
            # show a line of color == 0 for full lines if currently blinking off
            if blinking_off and all(pixel != 16 for pixel in line):  # short-circuit avoids heavy computation if not needed
                led_matrix.line((0,y), (led_matrix.width()-1, y), color=0)
            else:
                for x, pixel in enumerate(line):
                    led_matrix.point(x, y, pixel)
            
                    
    def remove_full_lines(self):
        """Removes lines that are full from stack
        @returns: number of full lines removed
        @rtype: int        
        """
        # TODO: this should be fast enough it doesn't cause problems while drawing
        score = 0
        for y, line in enumerate(self.points):
            if all(pixel != 16 for pixel in line):
                score += 1
                del self.points[y]
        return score
    

class Shape(object):
    """Shape names as described in U{http://en.wikipedia.org/wiki/Tetris}"""
    shapes = "IJLOSTZ"
    
    sprite = {}
    for shape in shapes:
        # store LEDSprite of tetris piece
        sprite[shape] = led_matrix.LEDSprite(os.path.abspath(shape + ".spr"))
    
    def valid(shape):
        return shape in shapes and len(shape) == 1

class Piece(object):

    def __init__(self, shape, pos=None):
        if not Shape.valid(shape):
            raise ValueError("Not a valid shape")
        if pos is None:
            pos = (led_matrix.width()/2, led_matrix.height() - 4)
        self.pos = pos
        self.sprite = Shape.sprite[shape].copy()  # get a copy of sprite
        
    def rotate(self, clockwise=True):
        """Rotates the piece clockwise or counter-clockwise"""
        # TODO: probably fix this, because I don't think it will rotate like I want it to
        if clockwise:
            self.sprite.rotate(90)
        else:
            self.sprite.rotate(270)
        
    def coverage(self, pos=None):
        """Returns the set of points that the piece is covering.
        @param pos: Set if we want to test the coverage as if the piece was at
            that location.
        @type pos: (x,y)
        @returns: A set of points that the piece is covering
        @rtype: set of 2 tuples
        """
        if pos is None:
            pos = self.pos
        coverage = set()
        for y, line in enumerate(self.sprite.bitmap):
            for x, pixel in enumerate(line):
                if pixel != 16:  # ignore transparent pixels in converage
                    coverage.add((pos[0] + x, pos[1] + y))
        return coverage
            
    def can_movedown(self):
        """Tests whether piece can move down without colliding with other piece
        or falling off edge (hit bottom)
        @rtype: boolean
        """
        if self is None:
            return False
        
        # check if it is at bottom of screen
        if (self.pos[1] + self.sprite.height) >= (led_matrix.height() - 1):
            return False
        
        # get coverage pretending we moved down
        pos = (self.pos[0], self.pos[1] + 1)
        self_coverage = self.coverage(pos)
        
        ret = None
        for piece in rested_pieces:
            # check if any coverage points of self and rested piece intersect
            if len(self_coverage.intersection(piece.coverage())) > 0:
                return False
                
        return True  # didn't find intersection for any rested piece, we can move down!
        
    def movedown(self):
        """Moves piece down one pixel."""
        self.pos = (self.pos[0], self.pos[1] + 1)
        
    def moveright(self):
        self.pos = (self.pos[0] + 1, self.pos[1])
    
    def moveleft(self):
        self.pos = (self.pos[0] - 1, self.pos[1])
        
    def draw(self):
        """Draws piece on led matrix"""
        led_matrix.sprite(self.sprite, self.pos)
        
   
class State(object):
    IDLE, RESET, MOVINGDOWN, BLINKING, DONE, EXIT = range(6)
    
curr_state = State.IDLE
curr_piece = None
stack = None
blinking_clock = 0

# setup buttons
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
SELECT = 22
START = 27
A = 4
B = 17

# what to do when button is pressed
def button_handler(channel):
    global curr_state
    if channel == START:
        curr_state = State.EXIT
        return
    if curr_state == State.MOVINGDOWN:
        if channel == LEFT:
            curr_piece.moveleft()
        elif channel == RIGHT:
            curr_piece.moveright()
        elif channel == A:
            curr_piece.rotate(90)
        elif channel == DOWN:
            # TODO: speed up piece
            pass
    elif (curr_state == State.IDLE or curr_state == State.DONE) and channel == A:
        curr_state = State.RESET

# set button handler to physical buttons 
GPIO.setmode(GPIO.BCM)
for button in [UP, DOWN, LEFT, RIGHT, SELECT, START, A, B]:
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=300)
        
while True:
    if curr_state == State.MOVINGDOWN:
        # check if stack hit the top of display
        if stack.height() >= led_matrix.height() - 1:
            curr_state = State.DONE
            continue
        
        # check if piece can't move down, and if so, add piece to stack and start blinking
        if not curr_piece.can_movedown():
            stack.add(curr_piece)
            curr_piece = None
            blinking_clock = BLINKING_TIME
            curr_state = State.BLINKING
            continue
            
        # otherwise move piece down
        curr_piece.movedown()
        
        # show screen
        led_matrix.erase()
        curr_piece.draw()
        stack.draw()
        led_matrix.show()
        time.sleep(1)
        # TODO:
        #  - detect if game is over by seeing if len(stack) >= led_matrix.height() - 1
        #  - figure out if curr_piece can move down
        #       - if so, move the piece down, delay, and then loop back around
        #   - else:
        #       - {don't move down for a couple of seconds incase
        #          the want to move to left or right}
        #       - add piece to stack, then before generating a new
        #           piece wait a little bit and turn blinking_off == True every other time  (make this a different state??)
        #          - then remove full lines and then generate next curr_piece, repeat
    elif curr_state == State.BLINKING:
        if blinking_clock == 0:
            score += stack.remove_full_lines()
            # make a new piece and go make to moving piece down
            curr_piece = Piece(random.choice("IJLOSTZ"))
            curr_state = State.MOVINGDOWN
        else:
            # draw blinking full lines (if any)
            # TODO: don't delay like this if no full lines?
            led_matrix.erase()
            stack.draw(blinking_off=(blinking_clock % 2))
            led_matrix.show()
            blinking_clock -= 1
            time.sleep(1)
        
    elif curr_state == State.IDLE:
        # TODO: scroll the text 
        led_matrix.erase()
        led_matrix.text("TETRIS")
        led_matrix.show()
        
    elif curr_state == State.RESET:
        score = 0
        stack = None
        stack = Stack()
        curr_piece = Piece(random.choice("IJLOSTZ"))
        curr_state = State.MOVINGDOWN
        
    elif curr_state == State.DONE:
        led_matrix.erase()
        led_matrix.text(str(score))
        led_matrix.show()
        
    elif curr_state == State.EXIT:
        GPIO.cleanup()
        led_matrix.cleanup()
        sys.exit(0)
        
        
