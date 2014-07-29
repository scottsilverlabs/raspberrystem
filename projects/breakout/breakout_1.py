#This is the first project in the breakout series, in this
#project the the user will learn how to make the class and
#physics for the paddle.

#Imports
from rstem import led_matrix
import accel
import time

#Initialize hardware
led_matrix.init_grid(2, 2)
accel.init(1)

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
	velocity = velocity*alpha + (angles[0]*8/90)*(1 - alpha)
#	Move player's paddle
	player_pos = player_pos + velocity
	player_pos = clamp(player_pos, 0, 15 - (p.size[0] - 1))
#	If the paddle hits the edge the velocity can't be into the edge
	if int(player_pos) <= 0 and velocity < 0:
		velocity = 0
	elif int(player_pos) >= 15 and velocity > 0:
		velcoity = 0
#	Move player and update physics
	p.move(player_pos)
#	Display paddle
	led_matrix.line(p.pos, [p.pos[0] + p.size[0] - 1, 0])
#	Display player and wait slightly
	led_matrix.show()
	time.sleep(0.01)
