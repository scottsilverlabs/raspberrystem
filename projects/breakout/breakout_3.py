#In this project the user adds the Ball class, which handles
#most of the game physics, and adds the win and lose functions.

#Imports
from rstem import led_matrix
from rstem import accel
import sys
import time

#Initialize hardware
led_matrix.init_grid(2, 2)
accel.init(1)

#Initialize game data
bricks = []
score = 0
start_time = time.time()
ball_tick = 0
MAX_BALL_TICK = 8
#Useful clamp function
def clamp(value, minimum, maximum):
	return min(maximum, max(value, minimum))

#Display losing score
def lose():
	string = "You lost! Score: %i" % (score)
	msg = led_matrix.LEDText(string, font_name='large')
	for i in range(len(string)*6 + 15):
		led_matrix.fill(0)
		led_matrix.text(msg, (15 - i, 7))
		led_matrix.show()
#		time.sleep(0.1)
	sys.exit(0)

#If all bricks are destroyed, display winning score
def win():
	string = "You won! Score: %i" % (score)
	msg = led_matrix.LEDText(string, font_name='large')
	for i in range(len(string)*6 + 15):
		led_matrix.fill(0)
		led_matrix.text(msg, (15 - i, 7))
		led_matrix.show()
	sys.exit(0)

#Simple class for player Paddle
class Paddle:

	def __init__(self, pos, size):
		self.pos = pos
		self.size = size

	def move(self, x):
		self.pos[0] = int(x)

#Declare paddle for use in ball class
p = Paddle([7, 0], [4, 0])

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
			win()
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
				lose()
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

#Initialize bricks
for x in range(4):
	for y in range(3):
		bricks.append(Brick([x*4, 15 - y*3 - 1],[3, 2]))
#Initialize ball
ball = Ball([8,1],[1,1])
#Initialize player movement data
velocity = 0.0
player_pos = 7.0
alpha = 0.1

while True:
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
