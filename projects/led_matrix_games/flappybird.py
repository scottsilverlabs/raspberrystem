
from rstem import led_matrix
import RPi.GPIO as GPIO
import time

BUTTON=4

# initialization
led_matrix.init_grid(1,2,270)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class Bird(object):

    def __init__(self, position=[3,3], speed=1, gravity_speed=1):
        self.speed = speed
        self.position = position
        self.flapping = False
        
    def x(self):
        return self.position[0]
    
    def y(self):
        return self.position[1]
        
    def flap(self, distance=3):
        distance = min(distance, led_matrix.height() - self.y())
        orig_x, orig_y = self.position
        self.flapping = True
        # flap up
        while self.y() <= (orig_y + distance):
            self.position[1] += 1
            time.sleep(1./self.speed)   # TODO: this probably doesn't work
        self.flapping = False
            
    def falldown(self):
        self.position[1] -= 1
        time.sleep(1./self.gravity_speed)
        
    def draw(self):
        led_matrix.point(self.x(), self.y())
        
class Pipe(object):

    def __init__(self, x_position=None, width=2, opening_height=4, opening_location=3):
        if x_position is None:
            self.x_position = led_matrix.width()
            
    def move_left(self, num_pixels=1):
        self.x_position -= num_pixels
        
    def collided_with(self, bird):
        """Checks if bird collided with pipe"""
        if self.x_position < bird.x() < (self.x_position + self.width):
            if (self.opening_location) < bird.y() < (self.opening_location + opening_height):
                return False
            else:
                return True
        else:
            return False
        
    def draw(self):
        for offset in range(self.width):
            x = self.x_position + offset
            led_matrix.line((x, 0), (x, self.opening_location-1))
            led_matrix.line((x, self.opening_location + self.opening_height), (x, led_matrix.height()))
            
# initialize variables        
class State():
    RESET, IDLE, PLAYING, END = range(4)
    
state = State.RESET
bird = None
pipes = []
pipe_start = 0
pipe_spacing = 3
pipe_tick = 0

def button_handler(channel):
    if state == State.RESET:
        pass  # do nothing
    elif state == State.IDLE:
        state = State.PLAYING
    elif state == State.PLAYING:
        bird.flap()
    elif state == State.END:
        state = State.RESET
        
GPIO.add_event_detect(BUTTON, GPIO.FALLING, callback=button_handler, bouncetime=300)
            
try:
    while True:
        if state == State.RESET:
            bird = Bird()
            pipes = []
            pipe_start = led_matrix.width()
            state = State.IDLE
        elif state == State.IDLE:
            led_matrix.erase()
            bird.draw()
            led_matrix.show()
        elif state == State.PLAYING:
            led_matrix.erase()
        
            # draw pipes
            for pipe in pipes:
                pipe.draw()
#            x = pipe_pos
#            for pipe in reversed(pipes):
#                if x < (-pipe.width): # stop drawing if off screen
#                    break
#                pipe.draw(x)
#                x -= pipe.width + pipe_spacing
                
            # let bird fall if not flapping up
            if not bird.flapping:
                bird.falldown()
            bird.draw()
            
            led_matrix.show()
            
            # move all pipes to the left one
            for pipe in pipes:
                pipe.move_left()
            pipe_tick += 1
            
            # add a new pipe
            if pipe_tick == pipe_spacing:
                pipe_tick = 0
                # TODO make random opening holes
                pipes.append(Pipe())
            
            # check for collision
            for pipe in pipes:
                if pipe.collided_with(bird):
                    state = State.END
                    break
            
        elif state == State.END:
            led_matrix.erase()
            led_matrix.text("Game Over")
            led_matrix.show()

finally:
    GPIO.cleanup()
    led_matrix.shutdown_matrices()


