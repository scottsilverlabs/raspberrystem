import RPi.GPIO as gpio
import time
from itertools import cycle

def kitt():
    gpio.setmode(gpio.BCM)
    leds = [14, 15, 23, 24, 25, 8, 7]
    for led in leds:
        gpio.setup(led, gpio.OUT)
        gpio.output(led, False)

    left = 2
    right = 3
    gpio.setup(left, gpio.IN, pull_up_down=gpio.PUD_UP)
    gpio.setup(right, gpio.IN, pull_up_down=gpio.PUD_UP)

    loops_per_move_list = cycle([1, 4, 10])
    loop_count = loops_per_move = next(loops_per_move_list)
    position = 0
    direction = 1
    right_was_pressed = False
    while True:
        if gpio.input(left) == 0:
            break
        right_is_pressed = gpio.input(right) == 0
        if not right_was_pressed and right_is_pressed:
            loop_count = loops_per_move = next(loops_per_move_list)
            print(loop_count)
        right_was_pressed = right_is_pressed
        loop_count -= 1
        if loop_count < 0:
            position += direction
            if position < 0:
                position = 0
                direction = 1
            elif position >= len(leds):
                position = len(leds) - 1
                direction = -1				
            loop_count = loops_per_move
        for led in leds:
            gpio.output(led, leds[position] == led)
    
        time.sleep(0.01)

    time.sleep(0.5)


def tug_of_war():
    gpio.setmode(gpio.BCM)
    leds = [14, 15, 23, 24, 25, 8, 7]
    for led in leds:
        gpio.setup(led, gpio.OUT)
        gpio.output(led, False)

    left = 2
    right = 3
    buttons = [left, right]
    was_pressed = {}
    is_pressed = {}
    for button in buttons:
        gpio.setup(button, gpio.IN, pull_up_down=gpio.PUD_UP)
        was_pressed[button] = False
        is_pressed[button] = False

    position = int(len(leds)/2)
    gpio.output(leds[position], True)
    presses = 0
    while 0 <= position < len(leds):
        for button in buttons:
            is_pressed[button] = gpio.input(button) == 0
            if not was_pressed[button] and is_pressed[button]:
                gpio.output(leds[position], False)
                if button == right:
                    position += 1
                else:
                    position -= 1
                if 0 <= position < len(leds):
                    gpio.output(leds[position], True)
            was_pressed[button] = is_pressed[button]
    
        time.sleep(0.03)

    if position < 0:
        led_to_flash = leds[0]
    else:
        led_to_flash = leds[-1]

    led_on = True
    count = 0
    any_pressed = False
    while not any_pressed:
        if count > 50:
            for button in buttons:
                if gpio.input(button) == 0:
                    any_pressed = True
    
        if count % 5 == 0:
            gpio.output(led_to_flash, led_on)
            led_on = not led_on
        count += 1
    
        time.sleep(0.03)

    time.sleep(0.5)

while True:
    kitt()
    tug_of_war()
    
    

