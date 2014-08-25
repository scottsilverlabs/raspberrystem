
#
# Copyright (c) 2014, Scott Silver Labs, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#Imports
from rstem import led_matrix
from rstem import accel
import RPi.GPIO as GPIO
import sys
import time

#Initialize hardware
led_matrix.init_grid()   # works best with a 2x2 matrix
accel.init(1)

#Initialize game data
bricks = []
ball = None
score = 0
start_time = time.time()
ball_tick = 0
MAX_BALL_TICK = 8

#Initialize player movement data
velocity = 0.0
player_pos = 7.0
alpha = 0.1

# Set up states for finite state machine
class State(object):
    PLAYING, IDLE, WIN, LOSE, RESET, EXIT = range(6)

# set current state
state = State.RESET

#Useful clamp function
def clamp(value, minimum, maximum):
	return min(maximum, max(value, minimum))
	
def scroll_text(string):
    """Scrolls the given text"""
    msg = led_matrix.LEDText(string, font_name='large')
    prev_state = state
    for i in range(len(string)*6 + 15):
        if state != prev_state:
            return  # leav if state has changed in the middle of scrolling
        led_matrix.erase()
        led_matrix.text(msg, (15 - i, 7))
        led_matrix.show()
        time.sleep(0.1)

#Simple class for player Paddle
class Paddle:

	def __init__(self, pos, size):
		self.pos = pos
		self.size = size

	def move(self, x):
		self.pos[0] = int(x)


#Class for ball which handles most game physics
class Ball:

	def __init__(self, pos, dir):
		self.pos = pos
		self.dir = dir
		self.bounced_x = False
		self.bounced_y = False
		self.can_move_x = True
		self.can_move_y = True
	
	def brick_col(self):
#		Loop through bricks and check for collisions
		for b in bricks:
			if b.xCol(self) and b.yCol(self):
#				If the ball hits a side edge reverse its x direction
				if self.pos[0] == b.pos[0] - 1:
					if self.bounced_x:
						self.can_move_x = False
					self.dir[0] = -1
					self.bounced_x = True
				elif self.pos[0] == b.pos[0] + b.size[0]:
					if self.bounced_x:
						self.can_move_x = False
					self.dir[0] = 1
					self.bounced_x = True
#				If the ball hits a side edge reverse its y direction
				if self.pos[1] == b.pos[1] - 1:
					if self.bounced_y:
						self.can_move_y = False
					self.dir[1] = -1
					self.bounced_y = True
				elif self.pos[1] == b.pos[1] + b.size[1]:
					if self.bounced_y:
						self.can_move_y = False
					self.dir[1] = 1
					self.bounced_y = True
#				Update score
				b.hit()

#	Update game physics
	def update(self):
		self.bounced_x = False
		self.bounced_y = False
		self.can_move_x = True
		self.can_move_y = True
#		Player wins if there are no more bricks
		if len(bricks) == 0:
			state = State.WIN
			return
#		Bounce off edge of screen
		if self.pos[1] >= 15 and self.dir[1] == 1:
			self.dir[1] = -1
		if self.pos[0] <= 0 and self.dir[0] == -1:
			self.dir[0] = 1
		if self.pos[0] >= 15 and self.dir[0] == 1:
			self.dir[0] = -1

#		Loop through bricks and check for collisions
		self.brick_col()

#		If one col check to see if we are inbetween two bricks
		if self.bounced_x or self.bounced_y:
			self.brick_col()

#		If the ball hits the paddle reverse its y direction							
		if (self.pos[1] + self.dir[1] == p.pos[1]) and (self.pos[0] + self.dir[0] >= p.pos[0]) and (self.pos[0] + self.dir[0] < p.pos[0] + p.size[0]):
			self.dir[1] = -self.dir[1]
#		Lose if the ball passes the paddle
		if self.pos[1] <= 0:
			for i in range(4):
				led_matrix.point(self.pos[0], self.pos[1])
				led_matrix.show()
				time.sleep(0.1)
				led_matrix.point(self.pos[0], self.pos[1], 0)
				led_matrix.show()
				time.sleep(0.1)
				state = State.LOSE
				return
		if self.can_move_x:
			self.pos[0] = clamp(self.pos[0] + self.dir[0], 0, 15)
		if self.can_move_y:
			self.pos[1] = clamp(self.pos[1] + self.dir[1], 0, 15)

#Class for brick
class Brick:
	def __init__(self, pos, size):
		self.pos = pos
		self.size = size
		self.brightness = 15

#	If hit increment score and decrement brightness
	def hit(self):
		global score
		self.brightness = self.brightness - 5
#		If the brightness is 0, remove brick
		if(self.brightness <= 0):
			bricks.remove(self)
		score = score + 1

#	Functions for collision detection
	def xCol(self, ball):
		return ((ball.pos[0] + ball.dir[0] >= self.pos[0]) and (ball.pos[0] + ball.dir[0] < self.pos[0] + self.size[0]))

	def yCol(self, ball):
		return ((ball.pos[1] + ball.dir[1] >= self.pos[1]) and (ball.pos[1] + ball.dir[1] < self.pos[1] + self.size[1]))


# Setup buttons
# setup buttons
UP = 25
DOWN = 24
LEFT = 23
RIGHT = 18
SELECT = 22
START = 27
A = 4
B = 17

# what to do during a button press
def button_handler(button):
    global curr_state
    if button == START:
        state = State.EXIT
    elif button == A:
        state = State.RESET


GPIO.setmode(GPIO.BCM)
for button in [A, START]:
    GPIO.setup(button, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.add_event_detect(button, GPIO.FALLING, callback=button_handler, bouncetime=300)


while True:
    if state == State.RESET:
        #Initialize bricks
        for x in range(4):
	        for y in range(3):
		        bricks.append(Brick([x*4, 15 - y*3 - 1],[3, 2]))
        #Initialize ball
        ball = Ball([8,1],[1,1])
        #Declare paddle for use in ball class
        p = Paddle([7, 0], [4, 0])
        state = state.PLAYING
        
    elif state = State.IDLE:
        # display breakout title
        msg = led_matrix.LEDText("BREAKOUT")
        x = led_matrix.width()
        while x > -msg.width:
            if state != State.IDLE:
                break
            led_matrix.erase()
            led_matrix.sprite(msg, (x, 0))
            led_matrix.show()
            x -= 1
            time.sleep(.1)

    elif state == State.PLAYING:
    #	Clear frame buffer
	    led_matrix.fill(0)
    #	Get angle data
	    angles = accel.angles()
    #	Simple lowpass filter for velocity data
	    velocity = velocity*alpha + (angles[0]*2*8/90)*(1 - alpha)
    #	Move player's paddle
	    player_pos = player_pos + velocity
	    player_pos = clamp(player_pos, 0, 15 - (p.size[0] - 1))
    #	If the paddle hits the edge the velocity can't be into the edge
	    if int(player_pos) <= 0 and velocity < 0:
		    velocity = 0
	    elif int(player_pos) >= 15 and velocity > 0:
		    velcoity = 0
    #	Move player
	    p.move(player_pos)
    #	Update physics
	    if ball_tick == 0:
		    ball.update()
    #	Display player, bricks, and the ball
	    led_matrix.line(p.pos, [p.pos[0] + p.size[0] - 1, 0])
	    for b in bricks:
		    for y in range(b.size[1]):
			    led_matrix.line((b.pos[0], b.pos[1]+y),(b.pos[0] + b.size[0] - 1, b.pos[1] + y), b.brightness)
	    led_matrix.point(ball.pos[0], ball.pos[1])
	    led_matrix.show()

    #	Delay and increase game tick
	    time.sleep(0.1)
	    ball_tick = (ball_tick + 1) & (MAX_BALL_TICK - 1)
	
    elif state == State.LOSE:
	    scroll_text("You lost! Score: %i" % (score))
        
    elif state == State.WIN:
	    scroll_text("You won! Score: %i" % (score))
    
    elif state == State.EXIT:
        led_matrix.cleanup()
        GPIO.cleanup()
        sys.exit(0)
	
	
	
