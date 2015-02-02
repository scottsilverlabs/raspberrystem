#!/usr/bin/env python3
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

import os
import re
import time
from . import led_driver     # c extension that controls led matrices and contains framebuffer
import copy
import subprocess
from itertools import islice

MAX_MATRICES = 4
MATRIX_SPI_SHIFT_REGISTER_LENGTH=32
width = 0    #: The width of the LED matrix grid
height = 0   #: The height of the LED matrix grid

def _valid_color(color):
    """Checks if given color is number between 0-16 if an int or 0-f, or - if string
    @param color: A color to check that is valid
    @type color: string or int
    """
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
    """Converts the given color to an int.
    @param color: A color to be converted
    @type color: string or int
    
    @raise ValueError: Fails L{_valid_color} check
    
    @return: Either the same int back again if color was an int or the int of a converted string
    @rtype: int
    """
    if not _valid_color(color):
        raise ValueError("Invalid Color: must be a string between 0-f or '-'" +
                         " or a number 0-16 with 16 being transparent")
    if type(color) == int:
        return color
    elif type(color) == str:
        if color == '-':
            return 0x10
        return int(color, 16)
    raise RuntimeError("Invalid color")


class Sprite(object):
    """Allows the creation of a LED Sprite that is defined in a text file.
    @note: The text file must only contain hex numbers 0-9, a-f, A-F, or - (dash)
    @note: The hex number indicates pixel color and "-" indicates a transparent pixel
    """
    def __init__(self, image_string):
        """Creates a L{Sprite} object from the given .spr file or image file or creates an empty sprite of given
        height and width if filename == None.
        
        @param filename: The full path location of a .spr sprite file or image file
        @type: string
        @param height: The height of given sprite if creating an empty sprite or want to resize a sprite from and image file.
        @type height: int
        @param width: The width of given sprite if creating an empty sprite or want to resize a sprite from and image file.
        @type width: int
        @param color: Color to display at point
        @type color: int or string (0-F or 16 or '-' for transparent)
        """
        # Remove whitespace from lines
        lines = (re.sub('\s', '', line) for line in image_string.splitlines())
        # remove blank lines
        lines = (line for line in lines if line)
        # Convert chars to integer colors
        reversed_transposed_bitmap = [[_convert_color(color) for color in line] for line in lines]
        # Reverse and transpose array
        transposed_bitmap = list(reversed(reversed_transposed_bitmap))
        self.bitmap = [list(z) for z in zip(*transposed_bitmap)]
        self.xcrop = range(self.width)
        self.ycrop = range(self.height)
        self.quarter_clockwise_rotations = 0
        self.flipped = False

    def _bitmap(self):
        if self.quarter_clockwise_rotations == 0:
            xrange = reversed(self.xcrop) if self.flipped else self.xcrop
            yrange = self.ycrop
            transposed = False
        elif self.quarter_clockwise_rotations == 1:
            xrange = reversed(self.xcrop) if self.flipped else self.xcrop
            yrange = reversed(self.ycrop)
            transposed = True
        elif self.quarter_clockwise_rotations == 2:
            xrange = reversed(self.xcrop) if not self.flipped else self.xcrop
            yrange = reversed(self.ycrop)
            transposed = False
        elif self.quarter_clockwise_rotations == 3:
            xrange = reversed(self.xcrop) if not self.flipped else self.xcrop
            yrange = self.ycrop
            transposed = True
        else:
            raise Exception("Internal Error: Invalid Sprite rotation")
        yrange = list(yrange)
        bitmap = [[self.bitmap[x][y] for y in yrange] for x in xrange]
        if transposed:
            bitmap = [list(z) for z in zip(*bitmap)]
        return bitmap

    @property
    def width(self):
        return len(self.bitmap)

    @property
    def height(self):
        return len(self.bitmap[0])

    def add(self, sprite, offset):
        """Appends given sprite to the right of itself.
        
        @param sprite: sprite to append
        @type sprite: L{Sprite}
        @note: height of given sprite must be <= to itself otherwise will be truncated
        """
        raise NotImplemented

    def crop(self, origin=(0,0), dimensions=None):
        x, y = origin
        if x >= self.width:
            raise IndexError("Origin X is greater than Sprite width")
        if y >= self.height:
            raise IndexError("Origin Y is greater than Sprite height")

        try:
            width, height = dimensions
        except TypeError:
            width, height = self.width, self.height

        self.xcrop = range(x, min(x + width, self.width))
        self.ycrop = range(y, min(y + height, self.height))
        return self

    def rotate(self, angle=90):
        """Rotates sprite at 90 degree intervals. 
        
        @returns: self
        @rtype: L{Sprite}
        
        @param angle: angle to rotate self in an interval of 90 degrees
        @type angle: int
        
        @returns: self
        @rtype: L{Sprite}
        @raises ValueError: If angle is not multiple of 90
        @note: If no angle given, will rotate sprite 90 degrees.
        """
        if angle % 90 != 0:
            raise ValueError("angle must be a multiple of 90.")
        self.quarter_clockwise_rotations = int(angle/90) % 4
        return self
        
    def flip(self):
        """Flips the sprite horizontally.

        flip vertical is equivalent to rotate(180).flip()
        """
        self.flipped = True
        return self
        
def _char_to_sprite(char, font_path):
    """Converts given character to a sprite.
    
    @param char: character to convert (must be of length == 1)
    @type char: string
    @param font_path: Relative location of font face to use.
    @type font_path: string
    @rtype: L{Sprite}
    """
    if not (type(char) == str and len(char) == 1):
        raise ValueError("Not a character")
    orig_font_path = font_path
    if char.isdigit():
        font_path = os.path.join(font_path, "numbers", char + ".spr")
    elif char.isupper():
        font_path = os.path.join(font_path, "upper", char + ".spr")
    elif char.islower():
        font_path = os.path.join(font_path, "lower", char + ".spr")
    elif char.isspace():
        font_path = os.path.join(font_path, "space.spr")
    else:
        font_path = os.path.join(font_path, "misc", str(ord(char)) + ".spr")
        
    if os.path.isfile(font_path):
        return Sprite(font_path)
    else:
        return Sprite(os.path.join(orig_font_path, "unknown.spr"))
        
        

class LEDText(Sprite):
    """A L{Sprite} object of a piece of text."""
    def __init__(self, message, char_spacing=1, font_name="small", font_path=None):
        """Creates a text sprite of the given string
        This object can be used the same way a sprite is useds
        
        @param char_spacing: number pixels between characters
        @type char_spacing: int
        @param font_name: Font folder (or .font) file to use as font face
        @type font_name: string
        @param font_path: Directory to use to look for fonts. If None it will used default directory in dist-packages
        @type font_path: string
        """
        if font_path is None: # if none, set up default font location
            this_dir, this_filename = os.path.split(__file__)
            # only use font_name if no custom font_path was given
            font_path = os.path.join(this_dir, "font")
            
        if not os.path.isdir(font_path):
            raise IOError("Font path does not exist.")
        orig_font_path = font_path

        # attach font_name to font_path
        font_path = os.path.join(font_path, font_name)
        
        # if font subdirectory doesn exist, attempt to open a .font file
        if not os.path.isdir(font_path):
            f = open(os.path.join(orig_font_path, font_name + ".font"), 'r')
            font_path = os.path.join(orig_font_path, f.read().strip())
            f.close()

        message = message.strip()
        if len(message) == 0:
            super().__init__()
            return

        # start with first character as intial sprite object
        init_sprite = _char_to_sprite(message[0], font_path)
        # get general height and width of characters

        if len(message) > 1:
            # append other characters to initial sprite
            for char in message[1:]:
                # add character spacing
                init_sprite.append(Sprite(height=init_sprite.height, width=char_spacing, color=0x10))
                # now add next character
                sprite = _char_to_sprite(char, font_path)
                if sprite.height != init_sprite.height:
                    raise ValueError("Height of character sprites must all be the same.")
                # append
                init_sprite.append(sprite)

        self.bitmap = init_sprite.bitmap

class FrameBuffer(object):
    def __init__(self, num_rows=None, matrix_list=None, spi_port=0):
        self.fb = [[0]*8 for i in range(8)]
        led_driver.init_spi(250000, spi_port)

    def _framebuffer(self):
        return self.fb

    def point(self, x, y=None, color=0xF):
        try:
            if y == None:
                x, y = x
            if x < 0 or y < 0:
                raise IndexError
            self.fb[x][y] = color
        except IndexError:
            pass

    def erase(self, color=0):
        for x in range(self.width):
            for y in range(self.height):
                self.fb[x][y] = color

    def line(self, point_a, point_b, color=0xF):
        """Create a line from point_a to point_b.
        Uses Bresenham's Line Algorithm U{http://en.wikipedia.org/wiki/Bresenham's_line_algorithm}
        @type point_a, point_b: (x,y) tuple
        @param color: Color to display at point
        @type color: int or string (0-F or 16 or '-' for transparent)
        """
        x1, y1 = point_a
        x2, y2 = point_b
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            self.point(x1, y1, color)
            if (x1 == x2 and y1 == y2) or x1 >= self.width or y1 >= self.height:
                break
            e2 = 2*err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def rect(self, origin, dimensions, fill=False, color=0xF):
        """Creates a rectangle from start point using given dimensions
        
        @param origin: The bottom left corner of rectange (if math_coords == True).
            The top left corner of rectangle (if math_coords == False)
        @type origin: (x,y) tuple
        @param dimensions: width and height of rectangle
        @type dimensions: (width, height) tuple
        @param fill: Whether to fill the rectangle or make it hollow
        @type fill: boolean
        @param color: Color to display at point
        @type color: int or string (0-F or 16 or '-' for transparent)
        """
        x, y = origin
        width, height = dimensions

        if fill:
            for x_offset in range(width):
                self.line((x + x_offset, y), (x + x_offset, y + height - 1), color)
        else:
            self.line((x, y), (x, y + height - 1), color)
            self.line((x, y + height - 1), (x + width - 1, y + height - 1), color)
            self.line((x + width - 1, y + height - 1), (x + width - 1, y), color)
            self.line((x + width - 1, y), (x, y), color)
        
    def show(self):
        flat = list(pixel for col in self.fb for pixel in col)
        even = flat[::2]
        odd = flat[1::2]
        bitstream = bytes(b[0] | (b[1] << 4) for b in zip(even, odd))
        x = led_driver.send(bitstream)

    @staticmethod
    def detect():
        '''Returns the number of matrices connected.  
        
        Requires matrices connected in a full chain from MOSI back to MISO on
        the Raspberry Pi.
        '''
        # Matrix chain forms one long shift-register, of N * B, where N is the
        # number of matrices, and B is the length of the shift-register in each
        # matrix (32 bytes)
        #
        # If we assume there is some MAX number of matrices we won't exceed, we
        # can detect the length by push a string of bytes longer than the max
        # through the chain.
        rand = os.urandom(32)
        recv = led_driver.send(rand + bytes(MAX_MATRICES * MATRIX_SPI_SHIFT_REGISTER_LENGTH))

        # Search the received bytes for the random sequence.  The offset
        # determines the number of matrices in the chain
        for i in range(MAX_MATRICES + 2):
            start = i*MATRIX_SPI_SHIFT_REGISTER_LENGTH
            end = start + MATRIX_SPI_SHIFT_REGISTER_LENGTH
            if rand == recv[start:end]:
                break
        if i > MAX_MATRICES:
            raise IOError("Could not determine length of LED Matrix chain.")

    @property
    def width(self):
        return 8

    @property
    def height(self):
        return 8

    def draw(sprite, origin=(0,0), crop_origin=(0,0), crop_dimensions=None):
        """Sets given sprite into the framebuffer.
        
        @param origin: Bottom left position to diplay text (top left if math_coords == False)
        @type origin: (x,y) tuple
        @param crop_origin: Position to crop into the sprite relative to the origin
        @type crop_origin: (x,y) tuple
        @param crop_dimensions: x and y distance from the crop_origin to display
            - Keep at None to not crop and display sprite all the way to top right corner
        @type crop_dimensions: (x,y) tuple
        """
        if type(sprite) == str:
            sprite = Sprite(sprite)
        elif type(sprite) != LEDText and type(sprite) != Sprite:
            raise ValueError("Invalid sprite")
        
        global width
        global height
        
        x_pos, y_pos = origin
        x_crop, y_crop = crop_origin
        
        # set up offset
        if x_crop < 0 or y_crop < 0:
            raise ValueError("crop_origin must be positive numbers")
        
        # set up crop
        if crop_dimensions is None:
            x_crop_dim, y_crop_dim = (sprite.width, sprite.height)   # no cropping
        else:
            x_crop_dim, y_crop_dim = crop_dimensions
            if x_crop_dim < 0 or y_crop_dim < 0:
                raise ValueError("crop_dimensions must be positive numbers")
            
        # set up start position
        x_start = x_pos + x_crop
        y_start = y_pos + y_crop 
        
        if x_start >= width or y_start >= height:
            return
            
        # set up end position
        x_end = min(x_pos + x_crop + x_crop_dim, width, x_pos + sprite.width)
        y_end = min(y_pos + y_crop + y_crop_dim, height, y_pos + sprite.height)
        
        # iterate through sprite and set points to led_driver
        y = max(y_start,0)
        while y < y_end:
            x = max(x_start, 0)
            while x < x_end:
                x_sprite = x - x_start + x_crop
                y_sprite = y - y_start + y_crop
                x_sprite = int(x_sprite)
                y_sprite = int(y_sprite)
                point((x, y), color=sprite.bitmap[y_sprite][x_sprite])
                x += 1
            y += 1

__all__ = ['FrameBuffer', 'Sprite']
        
