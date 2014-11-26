#In this project the user adds the brick class to the game
#along with the code to display them.

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

#Useful clamp function
def clamp(value, minimum, maximum):
	return min(maximum, max(value, minimum))

#Simple class for player Paddle
class Paddle:

	def __init__(self, pos, size):
		self.pos = pos
		self.size = size

	def move(self, x):
		self.pos[0] = int(x)

#Declare paddle for use in ball class
p = Paddle([7, 0], [4, 0])

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
		return (ball.pos[0] + ball.dir[0] >= self.pos[0]) and (ball.pos[0] + ball.dir[0] < self.pos[0] + self.size[0])

	def yCol(self, ball):
		return ((ball.pos[1] + ball.dir[1] >= self.pos[1]) and (ball.pos[1] + ball.dir[1] < self.pos[1] + self.size[1]))

#Initialize bricks
for x in range(4):
	for y in range(3):
		bricks.append(Brick([x*4, 15 - y*3 - 1],[3, 2]))

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
#	Display player and bricks
	led_matrix.line(p.pos, [p.pos[0] + p.size[0] - 1, 0])
	for b in bricks:
		for y in range(b.size[1]):
			led_matrix.line((b.pos[0], b.pos[1]+y),(b.pos[0] + b.size[0] - 1, b.pos[1] + y), b.brightness)
	led_matrix.show()

#	Slowly speed up, start with delay at 0.1 and reach 0 at 60s
	time.sleep(0.01)
