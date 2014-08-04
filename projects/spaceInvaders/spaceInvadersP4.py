#Imports, need sys for exit function
#This project finishes the game and adds winning
#losing and scoring functions.
from rstem import led_matrix
from rstem import accel
import RPi.GPIO as GPIO
import time
import sys

#Initialize matrix, accelerometer, and GPIO, the matrix layout and accelerometer channel may changes from user to user
led_matrix.init_grid(2,2)
accel.init(1)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#Game entity data
player_pos = [7, 0]
missles = []
enemies = []

#Game timing data, missles get updated and therefore move roughly sixty times faster than enemies initialy
game_tick = 0
game_tick_max = 64
enemy_tick = 60
start_time = time.time()

#Function to add missle at the players position to set of current missles
def fire_missle(channel):
	missles.append(Missle([int(round(player_pos[0])), int(round(player_pos[1]))],[0, 1]))

#Call fire_missle when fire button is pressed
GPIO.add_event_detect(4, GPIO.FALLING, callback=fire_missle, bouncetime = 300)

#Display losing message when an invader gets past the player then exit
def lose():
	GPIO.cleanup()
	text = "Game Over!"
	msg = led_matrix.LEDText(text, font_name="large")
	for i in range(len(text)*6 + 15):
		led_matrix.fill(0)
		led_matrix.text(msg, (15 - i,7))
		led_matrix.show()
		time.sleep(0.1)
	sys.exit(0)

#Display winning message when there are no more invaders left
def win():
	GPIO.cleanup()
	text = "You Won in %is" % (int(time.time()-start_time))
	msg = led_matrix.LEDText(text, font_name="large")
	for i in range(len(text)*6+15):
		led_matrix.fill(0)
		led_matrix.text(msg, (15-i, 7))
		led_matrix.show()
		time.sleep(0.1)
	sys.exit()

#Useful clamp function to make sure the data passed to point is on the matrix
def clamp(x):
	if(x > 15):
		x = 15
	if(x < 0):
		x = 0
	return x


#Missle keeps track of its current position and current direction
class Missle:
	
	def __init__(self, position, direction):
		self.pos = position
		self.dir = direction

#	Move missle on missle update tick
	def update(self):
		self.pos[0] = self.pos[0] + self.dir[0]
		self.pos[1] = self.pos[1] + self.dir[1]
		if self.pos[1] > 15 or self.pos[1] < 0 or self.pos[0] < 0 or self.pos[1] > 15:
			missles.remove(self)

#Enemy keeps track of its current position and direction
class Enemy:

	def __init__(self, position, direction):
		self.pos = position
		self.dir = direction
	
	def update(self):
		self.pos[0] = self.pos[0] + self.dir[0]
		self.pos[1] = self.pos[1] + self.dir[1]
#		If it hits a wall move down two and change direction
		if self.pos[0] > 15:
			self.pos = [15, self.pos[1]-2]
			self.dir = [-1, 0]
		elif self.pos[0] < 0:
			self.pos = [0, self.pos[1]-2]
			self.dir = [1, 0]
#		If an enemy makes it past the player call the lose function
		if self.pos[1] < 0:
			lose()

#Setup initial enemies
for i in range(5):
	enemies.append(Enemy([i*3, 15], [1, 0]))
for i in range(5):
	enemies.append(Enemy([15-i*3 , 13], [-1, 0]))

#Start game
while True:

#	Clear previous framebuffer	
	led_matrix.fill(0)

#	Player wins if no more enemies are left
	if len(enemies) == 0:
		win()

#	Redraw enemies and update if its their game tick
	for e in enemies:
		if game_tick%enemy_tick == 0 and not game_tick == 0:
			e.update()
		led_matrix.point(e.pos[0], e.pos[1])

#	Update and redraw missles
	for m in missles:
		m.update()	
		led_matrix.point(m.pos[0], m.pos[1])

#	Check for collisions
	for m in missles:
		for e in enemies:
			if m.pos == e.pos:
				enemies.remove(e)
				missles.remove(m)
#	Get angles from accelerometer
	data = accel.angles()

#   Generate smooth movement data using IIR filter, and make a 1/4 turn move
#   the player to the edge of the screen
	player_pos[0] = player_pos[0] + (clamp(-data[0]*8*4/90 + 7) - player_pos[0])*0.1
	
#	Draw player
	led_matrix.point(int(round(player_pos[0])), int(round(player_pos[1])))

#	Show framebuffer
	led_matrix.show()

#	Delay one game tick, in this case 1ms
	time.sleep(0.001)

#	Make enemies speed up when their are less of them
	enemy_tick = int(len(enemies)*3)

#	Update game tick and wrap around
	game_tick = (game_tick+1)&(game_tick_max-1)
