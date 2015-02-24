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
SPI_SPEED=250000
width = 0    #: The width of the LED matrix grid
height = 0   #: The height of the LED matrix grid


def _to_color(color):
    '''Converts the given color to an int.
    @param color: A color to be converted
    @type color: string or int
    
    @raise ValueError: Fails L{_valid_color} check
    
    @return: Either the same int back again if color was an int or the int of a converted string
    @rtype: int
    '''
    if not (isinstance(color, str) and len(color) == 1 and color in '01234567890abcdefABCDEF-'):
        raise ValueError("Invalid Color: must be a string between 0-9 or a-f or '-'")
    return int(color, 16) if color != '-' else -1

def _color_array_to_str(array, height, width):
    s = ''
    for y in reversed(range(height)):
        for x in range(width):
            color = array[x][y]
            s += '{:1X}'.format(color) if color >= 0 else '-'
        s += '\n'
    return s

def _quarter_clockwise_rotations(angle):
    if angle % 90 != 0:
        raise ValueError('angle must be a multiple of 90.')
    return int(angle/90) % 4

class Sprite(object):
    '''Allows the creation of a LED Sprite that is defined in a text file.
    @note: The text file must only contain hex numbers 0-9, a-f, A-F, or - (dash)
    @note: The hex number indicates pixel color and "-" indicates a transparent pixel
    '''
    def __init__(self, image_string):
        '''Creates a L{Sprite} object from the given .spr file or image file or creates an empty sprite of given
        height and width if filename == None.
        
        @param filename: The full path location of a .spr sprite file or image file
        @type: string
        @param height: The height of given sprite if creating an empty sprite or want to resize a sprite from and image file.
        @type height: int
        @param width: The width of given sprite if creating an empty sprite or want to resize a sprite from and image file.
        @type width: int
        @param color: Color to display at point
        @type color: int or string (0-F or 16 or '-' for transparent)
        '''
        # Remove whitespace from lines
        lines = (re.sub('\s', '', line) for line in image_string.splitlines())
        # remove blank lines
        lines = (line for line in lines if line)
        # Convert chars to integer colors
        reversed_transposed_bitmap = [[_to_color(color) for color in line] for line in lines]
        # Reverse and transpose array
        transposed_bitmap = list(reversed(reversed_transposed_bitmap))
        self.original_bitmap = [list(z) for z in zip(*transposed_bitmap)]
        self.bitmap = self.original_bitmap

    @classmethod
    def from_file(cls, filename):
        with open(filename) as f:
            s = cls(f.read())
        return s
        
    def _bitmap(self):
        return self.bitmap

    @property
    def width(self):
        return len(self.bitmap)

    @property
    def height(self):
        return len(self.bitmap[0])

    def __add__(self, sprite):
        if self.height != sprite.height:
            raise ValueError("Can only add sprites of the same height")
        self.bitmap += sprite.bitmap
        return self

    def _recreate_bitmap(self, xrange, yrange):
        yrange = list(yrange)
        self.bitmap = [[self.bitmap[x][y] for y in yrange] for x in xrange]

    def crop(self, origin=(0,0), dimensions=None):
        x, y = origin
        if x >= self.width:
            raise IndexError('Origin X is greater than Sprite width')
        if y >= self.height:
            raise IndexError('Origin Y is greater than Sprite height')

        try:
            width, height = dimensions
        except TypeError:
            width, height = self.width, self.height

        xrange = range(x, min(x + width, self.width))
        yrange = range(y, min(y + height, self.height))
        self._recreate_bitmap(xrange, yrange)
        return self

    def rotate(self, angle=90):
        '''Rotates sprite at 90 degree intervals. 
        
        @returns: self
        @rtype: L{Sprite}
        
        @param angle: angle to rotate self in an interval of 90 degrees
        @type angle: int
        
        @returns: self
        @rtype: L{Sprite}
        @raises ValueError: If angle is not multiple of 90
        @note: If no angle given, will rotate sprite 90 degrees.
        '''
        quarter_clockwise_rotations = _quarter_clockwise_rotations(angle)
        if quarter_clockwise_rotations == 0:
            xrange, yrange = range(self.width), range(self.height)
            transposed = False
        elif quarter_clockwise_rotations == 1:
            xrange, yrange = range(self.width), reversed(range(self.height))
            transposed = True
        elif quarter_clockwise_rotations == 2:
            xrange, yrange = reversed(range(self.width)), reversed(range(self.height))
            transposed = False
        elif quarter_clockwise_rotations == 3:
            xrange, yrange = reversed(range(self.width)), range(self.height)
            transposed = True
        else:
            raise RuntimeException('Internal Error: Invalid rotation')
        self._recreate_bitmap(xrange, yrange)
        if transposed:
            self.bitmap = [list(z) for z in zip(*self.bitmap)]
        return self
        
    def flip(self, vertical=False):
        '''Flips the sprite horizontally.
        '''
        if vertical:
            xrange, yrange = range(self.width), reversed(range(self.height))
        else:
            xrange, yrange = reversed(range(self.width)), range(self.height)
        self._recreate_bitmap(xrange, yrange)
        return self

    def __str__(self):
        return _color_array_to_str(self.bitmap, self.height, self.width)

    def reset(self):
        '''Undoes previous flip/rotate/crop/etc actions
        '''
        self.bitmap = self.original_bitmap
        return self
        
class Text(Sprite):
    def __init__(self, message, char_spacing=1, font_name='5x7', font_dir=None):
        with open(self._font_path(font_dir, font_name, message[0])) as f:
            super().__init__(f.read())
        if len(message) > 1:
            self.__add__(Sprite((('-' * char_spacing) + '\n') * self.height))
            self.__add__(Text(message[1:]))

    @classmethod
    def from_file(cls, filename):
        super().from_file(filename)
        
    @classmethod
    def font_list(cls, font_dir=None):
        font_dir = cls._font_dir(font_dir)
        return [d for d in os.glob(font_dir) if os.path.isdir(d)]

    @staticmethod
    def _font_dir(font_dir=None):
        if font_dir is None:
            this_dir, this_filename = os.path.split(__file__)
            font_dir = os.path.join(this_dir, 'font')
            
        if not os.path.isdir(font_dir):
            raise IOError('Font path does not exist.')

        return font_dir
        
    def _font_path(self, font_dir, font_name, char):
        font_path = os.path.join(self._font_dir(), font_name)
        unknown_font_path = os.path.join(font_path, 'unknown.spr')
        
        if char.isdigit():
            font_path = os.path.join(font_path, 'numbers', char + '.spr')
        elif char.isupper():
            font_path = os.path.join(font_path, 'upper', char + '.spr')
        elif char.islower():
            font_path = os.path.join(font_path, 'lower', char + '.spr')
        elif char.isspace():
            font_path = os.path.join(font_path, 'space.spr')
        else:
            font_path = os.path.join(font_path, 'misc', str(ord(char)) + '.spr')
            
        if not os.path.isfile(font_path):
            return unknown_font_path

        return font_path

class FrameBuffer(object):
    def __init__(self, matrix_layout=None, spi_port=0):
        if not matrix_layout:
            num_matrices = self.detect(spi_port)
            if num_matrices == 0:
                raise('No LED Matrices connected')
            elif num_matrices > 8:
                raise('More than 8 LED Matrices connected - you must define the matrix_layout')
            else:
                matrix_layout = {
                    1 : [(x*8,0,0) for x in range(1)],
                    2 : [(x*8,0,0) for x in range(2)],
                    3 : [(x*8,0,0) for x in range(3)],
                    4 : [(x*8,8,0) for x in range(2)] + [(x*8,0,180) for x in reversed(range(2))],
                    5 : [(x*8,0,0) for x in range(5)],
                    6 : [(x*8,8,0) for x in range(3)] + [(x*8,0,180) for x in reversed(range(3))],
                    7 : [(x*8,8,0) for x in range(4)] + [(x*8,0,180) for x in reversed(range(3))],
                    8 : [(x*8,8,0) for x in range(4)] + [(x*8,0,180) for x in reversed(range(4))],
                }[num_matrices]
        xlist = [x for x,y,angle in matrix_layout]
        ylist = [y for x,y,angle in matrix_layout]
        maxx, maxy = max(xlist), max(ylist)
        minx, miny = min(xlist), min(ylist)
        if minx < 0 or miny < 0:
            raise ValueError('All matrix_layout origins must be greater than zero (x and y)')

        # Convert angles to quarter_clockwise_rotations
        matrix_layout = \
            [(x, y, _quarter_clockwise_rotations(angle)) for x, y, angle in matrix_layout]

        self.matrix_layout = matrix_layout
        self.fb = [[0]*(maxy + 8) for i in range(maxx + 8)]
        led_driver.init_spi(SPI_SPEED, spi_port)

    def _framebuffer(self):
        return self.fb

    def point(self, x, y=None, color=0xF):
        try:
            if y == None:
                x, y = x
            if x < 0 or y < 0:
                raise IndexError
            if color >= 0:
                self.fb[x][y] = color
        except IndexError:
            pass

    def erase(self, color=0):
        for x in range(self.width):
            for y in range(self.height):
                self.fb[x][y] = color

    def line(self, point_a, point_b, color=0xF):
        '''Create a line from point_a to point_b.
        Uses Bresenham's Line Algorithm U{http://en.wikipedia.org/wiki/Bresenham's_line_algorithm}
        @type point_a, point_b: (x,y) tuple
        @param color: Color to display at point
        @type color: int or string (0-F or 16 or '-' for transparent)
        '''
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
        '''Creates a rectangle from start point using given dimensions
        
        @type origin: (x,y) tuple
        @param dimensions: width and height of rectangle
        @type dimensions: (width, height) tuple
        @param fill: Whether to fill the rectangle or make it hollow
        @type fill: boolean
        @param color: Color to display at point
        @type color: int or string (0-F or 16 or '-' for transparent)
        '''
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
        bitstream = b''
        for xoff, yoff, quarter_clockwise_rotations in reversed(self.matrix_layout):
            forward = range(8)
            backward = reversed(range(8))
            if quarter_clockwise_rotations == 0:
                flat = [self.fb[xoff + x][yoff + y] for x in forward for y in forward]
            elif quarter_clockwise_rotations == 1:
                flat = [self.fb[xoff + x][yoff + y] for y in backward for x in forward]
            elif quarter_clockwise_rotations == 2:
                flat = [self.fb[xoff + x][yoff + y] for x in backward for y in backward]
            elif quarter_clockwise_rotations == 3:
                flat = [self.fb[xoff + x][yoff + y] for y in forward for x in backward]
            else:
                raise RuntimeException('Internal Error: Invalid rotation')
            even = flat[::2]
            odd = flat[1::2]
            bitstream += bytes(b[0] | (b[1] << 4) for b in zip(even, odd))
        led_driver.send(bitstream)

    @staticmethod
    def detect(spi_port=0):
        '''Returns the number of matrices connected.  
        
        Requires matrices connected in a full chain from MOSI back to MISO on
        the Raspberry Pi.
        '''
        led_driver.init_spi(SPI_SPEED, spi_port)

        # Matrix chain forms one long shift-register, of N * B, where N is the
        # number of matrices, and B is the length of the shift-register in each
        # matrix (32 bytes)
        #
        # If we assume there is some MAX number of matrices we won't exceed, we
        # can detect the length by push a string of bytes longer than the max
        # through the chain.
        rand = os.urandom(32)
        sequence = rand + bytes(MAX_MATRICES * MATRIX_SPI_SHIFT_REGISTER_LENGTH)
        recv = led_driver.send(sequence)

        # Search the received bytes for the random sequence.  The offset
        # determines the number of matrices in the chain
        for i in range(MAX_MATRICES + 2):
            start = i*MATRIX_SPI_SHIFT_REGISTER_LENGTH
            end = start + MATRIX_SPI_SHIFT_REGISTER_LENGTH
            if rand == recv[start:end]:
                break
        if i > MAX_MATRICES:
            raise IOError('Could not determine length of LED Matrix chain.')
        return i

    @property
    def width(self):
        return len(self.fb)

    @property
    def height(self):
        return len(self.fb[0])

    def __str__(self):
        return _color_array_to_str(self.fb, self.height, self.width)

    def draw(self, drawable, origin=(0,0)):
        '''Sets given sprite into the framebuffer.
        '''
        xorig, yorig = origin
        bitmap = drawable._bitmap()
        if not bitmap:
            return
        width, height = len(bitmap), len(bitmap[0])
        for x in range(width):
            for y in range(height):
                self.point(xorig + x, yorig + y, bitmap[x][y])

__all__ = ['FrameBuffer', 'Sprite']
        
