#!/usr/bin/python3

import os
# import bitstring
import re
import time
from itertools import islice
# from scipy import misc
# import numpy
# import magic
import led_driver     # c extension that controls led matrices and contains frame buffer

# global variables for use
SIZE_OF_PIXEL = 4     # 4 bits to represent color
DIM_OF_MATRIX = 8     # 8x8 led matrix elements
initialized = False   # flag to indicate if LED has been initialized
contianer_width = 0    # indicates the maximum width and height of the LEDContainer
container_height = 0

# run demo program if run by itself
def _main():
    while 1:
        for i in range(8):
            for j in range(8):
                mat = LEDMatrix()
                mat.point(x, y)
                mat.show()
                time.sleep(0.5);
                mat.point(x, y, color=0)

if __name__ == "__main__":
    _main()



def _init_check():
    """Checks that initMatrices has been called and throws an error if not"""
    global initialized
    if not initialized:
        raise RuntimeError("Matrices must be initialized first.")

def _valid_color(color):
    if type(color) == int:
        if color < 0x0 or color > 0x10:
            return False
        return True
    elif type(color) == str:
        if not re.match(r'^[A-Za-z0-9-]$', color):
            return False
        return True
    return False

def _convert_color(color):
    if not _valid_color(color):
        raise ValueError("Invalid Color: must be a string between 0-f or '-'" +  \
            " or a number 0-16 with 16 being transparent")
    if type(color) == int:
        return color
    if color == '-':
        return 0x10
    return int(color, 16)

def initMatrices(mat_list=[(0,0,0)], spi_speed=500000, spi_port=0):
    """Create a chain of led matrices set at particular offsets into the frame buffer
    The order of the led matrices in the list indicate the order they are
    physically hooked up with the first one connected to Pi.
    mat_list = list of tuple that contains led matrix and offset
        ex: [(0,0,led1),(7,0,led2)]"""
    # if mat_list is None:
    #     mat_list = [(0,0,0)] # set up a single matrix
    # if already initialized clean up old initialization first
    global initialized
    if initialized:
        close()
    container_width = max([matrix[0] for matrix in mat_list]) + DIM_OF_MATRIX
    container_height = max([matrix[1] for matrix in mat_list]) + DIM_OF_MATRIX
    flat_mat_list = [item for tuple in mat_list for item in tuple]
    led_driver.initMatrices(flat_mat_list, len(mat_list), \
        container_width, container_height) # flatten out tuple
    led_driver.initSPI(spi_speed, spi_port)
    initialized = True

def show():
    _init_check()
    led_driver.flush()

# TODO: call this "unInitLED" instead?
def close():
    """Unintializes matrices and frees all memory"""
    global initialized
    if not initialized:
        return
    led_driver.fill(0x0)
    led_driver.flush()
    led_driver.close()

def fill(color=0xF):
    _init_check()
    led_driver.fill(_convert_color(color))

# def line(point_a, point_b, color=0xF):
#     led_driver.line(*point_a, *point_b, color)

def point(self, x, y=None, color=0xF):
    """Adds point to bitArray and foreground or background sprite"""
    _init_check()
    if x < 0 or x >= container_width or y < 0 or y >= container_height:
        raise IndexError("Point given is not in framebuffer.")
    # If y is not given, then x is a tuple of the point
    # if y is None and type(x) is tuple:
    #     x, y = x
    led_driver.point(x, y, _convert_color(color))

def rect(self, start, dimensions, color=0xF):
    """Creates a rectangle from start point using given dimensions"""
    x, y = start
    width, height = dimensions
    line((x, y), (x, y + height), color)
    line((x, y + height), (x + width, y + height), color)
    line((x + width, y + height), (x + width, y), color)
    line((x + width, y), (x, y), color)


def _sign(self, n):
    return 1 if n >= 0 else -1


def line(self, point_a, point_b, color=0xF):
    """Create a line from point_a to point_b"""
    # if color < 0x0 or color > 0xF:
    #     raise ValueError("Invalid color")

    x_diff = point_a[0] - point_b[0]
    y_diff = point_a[1] - point_b[1]
    step = self._sign(x_diff) * self._sign(y_diff)
    width = abs(x_diff) + 1
    height = abs(y_diff) + 1
    if (width > height):
        start_point = point_a if x_diff < 0 else point_b
        start_x, start_y = start_point
        for x_offset in range(width):
            led_driver.point(
                start_x + x_offset,
                start_y + step*(x_offset*height/width),
                _convert_color(color)
            )
    else:
        start_point = point_a if y_diff < 0 else point_b
        start_x, start_y = start_point
        for y_offset in range(height):
            led_driver.point(
                start_x + step*(y_offset*width/height),
                start_y + y_offset,
                _convert_color(color)
            )


def text(self, text, position=(0,0), offset_into=(0,0), crop=None, scrolling=False):
    """Sets given string to be displayed on LED Matrix
        - returns the LEDMessage sprite object used to create text
    """
    if type(text) == str:
        text = LEDMessage(text)
    elif type(text) != LEDMessage and type(text) != LEDSprite:
        raise ValueError("Invalid text")
    sprite(text, position, offset_into, crop)
    # TODO: remove scrolling, let it be a user program
    if scrolling:
        fill(0x0)  # clear screen first
        x_offset = offset_into[0]
        y_offset = offset_into[1]
        while 1:
            if (x + text.width) < 0: # reset x
                x = self.width
            x_offset += 1
            sprite(text, position, (x_offset, y_offset))
            show()
            x -= 1
    return text


def sprite(self, sprite, position=(0,0), offset_into=None, crop=None):
    """Sets given sprite with top left corner at given position"""
    _init_check()
    # set offset to 0 if an offset into sprite is negative
    if offset_into is not None:
        for i in range(2):
            if offset_into[i] < position[i]:
                offset_into[i] = position[i]
    # set up start position
    y_start = y if y >= 0 else 0
    x_start = x if x >= 0 else 0

    # set up end position
    if crop is not None:
        if crop[0] >= x_start and crop[0] < container_width:
            x_end = crop[0]
        else:
            x_end = container_width - 1
        if crop[1] >= y_start and crop[1] < container_height:
            y_end = crop[1]
        else:
            y_end = container_height - 1
    else:
        x_end, y_end = container_width - 1, container_height - 1

    # iterate through sprite and set points to led_driver
    y = y_start
    while y <= y_end:
        x = x_start
        while x <= x_end:
            point(x, y, sprite.bitmap[y][x])
            x += 1
        y += 1


class LEDSprite(object):
    """Allows the creation of a LED Sprite that is defined in a text file.
        - The text file must only contain hex numbers 0-9, a-f, A-F, or - (dash)
        - The hex number indicates pixel color and "-" indicates a transparent pixel
    """
    def __init__(self, filename=None, height=0, width=0, color=0x0):
        self.filename = filename
        bitmap = []
        bitmap_width = 0  # keep track of width and height
        bitmap_height = 0
        if filename is not None:
            f = open(filename, 'r')
            for line in f:
                if not re.match(r'^[0-9a-fA-F\s-]+$', line):
                    raise ValueError("Sprite file contains invalid characters")
                leds = [_convert_color(char) for char in line.split()]
                # Determine if widths are consistent
                if bitmap_width != 0:
                    if len(leds) != bitmap_width:
                        raise ValueError("Sprite has different widths")
                else:
                    bitmap_width = len(leds)
                bitmap.append(leds)
                bitmap_height += 1
            f.close()
        else:
            bitmap = [[color for i in range(width)] for j in range(height)]
            bitmap_height = height
            bitmap_width = width

        self.bitmap = bitmap
        self.height = bitmap_height
        self.width = bitmap_width

    def append(self, sprite):
        """Appends given sprite to the right of itself
            - height of given sprite must be <= to itself otherwise will be truncated
        """
        for i, line in enumerate(self.bitmap):
            if i >= sprite.height:
                # fill in with transparent pixels
                tran_line = [0x10 for j in range(sprite.width)]
                self.bitmap[i] = sum([line, tran_line], [])
            else:
                self.bitmap[i] = sum([line, sprite.bitmap[i]], [])
        # update size
        self.width += sprite.width

    def set_pixel(self, point, color=0xF):
        """Sets given color to given x and y coordinate in sprite
            - color can be a int or string of hex value
            - return None if coordinate is not valid
        """
        x, y = point
        if x >= self.width or y >= self.height or x < 0 or y < 0:
            return None
        self.bitmap[y][x] = _convert_color(color)

    def get_pixel(self, x, y):
        """Returns int of color at given position or None
        """
        if x >= self.width or y >= self.height or x < 0 or y < 0:
            return None
        return self.bitmap[y][x]


    def save_to_file(self, filename):
        pass
        # TODO: save sprite to file?


def _char_to_sprite(char, font_location, space_size=(7,5)):
    if not (type(char) == str and len(char) == 1):
        raise ValueError("Not a character")
    if char.isdigit():
        return LEDSprite(font_location + "/number/" + char)
    elif char.isupper():
        return LEDSprite(font_location + "/upper/" + char)
    elif char.islower():
        return LEDSprite(font_location + "/lower/" + char)
    elif char.isspace():
        return LEDSprite(height=space_size[0], width=space_size[1], color=0x10)
    else:
        raise ValueError("Invalid character")


class LEDMessage(LEDSprite):

    def __init__(self, message, char_spacing=1, font_location="font"):
        """Creates a text sprite of the given string
            - This object can be used the same way a sprite is used
            char_spacing = number pixels between characters
            font_location = location of folder where font bitmaps are located
        """
        message = message.strip()
        if len(message) == 0:
            super(LEDSprite, self).__init__()
            return
        if not re.match(r'^[A-Za-z0-9\s]+$', message):
            raise ValueError("Message contains invalid characters. Only A-Z, a-z, 0-9, -, and space")
        # start with first character as intial sprite object
        init_sprite = _char_to_sprite(message[0], font_location)
        bitmap = init_sprite.bitmap
        # get general height and width of characters
        height = init_sprite.height
        width = init_sprite.width

        if len(message) > 1:
            # append other characters to initial sprite
            for char in message[1:]:
                # add character spacing
                init_sprite.append(
                        LEDSprite(height=height, width=char_spacing, color=0x10))
                sprite = _char_to_sprite(char, font_location, space_size=(height, width))
                if sprite.height != height:
                    raise ValueError("Height of character sprites must all be the same.")
                # append
                init_sprite.append(sprite)

        self.bitmap = init_sprite.bitmap
        self.height = init_sprite.height
        self.width = init_sprite.width
