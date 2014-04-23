#
# marquee.py
#
# Create a marquee sign - a string of dots that rotates around the border of
# the LED matrices.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the
# Free Software Foundation.  See the file COPYING included with this software
# for the full license.
#
# Copyright (c) 2014 Brian Silverman, Scott Silver Labs
#
#
import time
from rstem import led

# Create a list of points, that are all the points of the marquee border, in
# order.
max_width = led.width() - 1
max_height = led.height() - 1
top = [(x, max_height) for x in range(max_width)]
right = [(max_width, max_height-y) for y in range(max_height)]
bottom = [(max_width-x, 0) for x in range(max_width)]
left = [(0, y) for y in range(max_height)]
marquee = top + right + bottom +  left
percent_on = 30

while True:
    # For each point in the marquee, up to the defined percent_on, draw the
    # point
    led.erase()
    for i, point in enumerate(marquee):
        if i % len(marquee) < (percent_on/100.0) * len(marquee):
            led.point(point)
    led.show()
    time.sleep(0.1);

    # Rotate all the points in the marquee
    marquee = marquee[1:] + [marquee[0]]
