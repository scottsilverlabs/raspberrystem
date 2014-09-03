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
import time
from rstem import led_matrix

x = 0.0
y = 0.0
xdist = 0.1
ydist = 0.5
period = 0.01
sprite_period = 0.2
sprite_steps = sprite_period/period
step = 0
sprites = [led_matrix.LEDSprite("ball%d.spr" % i) for i in range(4)]
while True:
    # Draw the ball
    sprite = sprites[n]
    led_matrix.erase()
    led_matrix.sprite(sprite, (x, y))
    led_matrix.show()

    # Change to next sprite, once every sprite_steps
    step += 1
    if step % sprite_steps == 0:
        n = (n + 1) % len(sprites)

    # Move the point to a new position.  If it hits a wall, reverse the
    # direction of the ball.
    x, y = (x+xdist, y+ydist)
    if x >= (led_matrix.width() - (sprite.width() - 1)) or x < 0:
        xdist = - xdist
    if y >= (led_matrix.height() - (sprite.height() - 1)) or y < 0:
        ydist = - ydist

    time.sleep(period)

