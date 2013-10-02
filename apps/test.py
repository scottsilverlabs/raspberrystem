import time
import led
import math

"""
for i in range(1):
    for x in range(8):
        for y in range(8):
            led.point(x, y)
            led.show()
            time.sleep(0.1);
            led.point(x, y, color=0)
"""

"""
for x1 in range(8):
    for y1 in range(8):
        for x2 in range(8):
            for y2 in range(8):
                led.line((x1,y1), (x2,y2))
                led.show()
                time.sleep(0.005);
                led.erase()
"""
"""
for x1 in range(8):
    for y1 in range(8):
        for x2 in range(8):
            for y2 in range(8):
                led.rect((x1,y1), (x2,y2))
                led.show()
                time.sleep(0.05);
                led.erase()
"""
def new_vector(ball, direction, speed, time, width=8.0, height=8.0):
    x, y = ball
    distance = speed * time
    x = x + distance * math.cos(math.radians(direction))
    y = y + distance * math.sin(math.radians(direction))
    if x >= width:
        x = 2 * width - x
        direction = 180 - direction
    if x < 0:
        x = -x
        direction = 180 - direction
    if y >= height:
        y = 2 * height - y
        direction = -direction
    if y < 0:
        y = - y
        direction = -direction
    return ((x, y), direction)
    
ball = (0.0, 0.0)
direction = 70.0
speed = 100.0
period = 0.01
dimensions = (1,1)
while True:
    led.rect(ball, dimensions)
    led.show()
    time.sleep(period);
    led.rect(ball, dimensions, color=0)
    ball, direction = new_vector(ball, direction, speed, period, width=7, height=7)

