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
'''
This module provides interfaces to the LED Matrix RaspberrySTEM Cell.
'''


import os
import re
import time
from . import led_driver     # c extension that controls led matrices and contains framebuffer
import copy
import subprocess
from itertools import islice

MAX_MATRICES = 64
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
    '''A Sprite (2-dimensional bitmapped image) object.

    A `Sprite` is drawable on the LED Matrix `FrameBuffer` with the
    `FrameBuffer`'s `draw()` function.  `Sprite`s support tranparency.

    Two sprites of the same hieght can be added togther, creating a new
    horizontally concatenated composite sprite.
    '''
    def __init__(self, image_string):
        '''Creates a `Sprite` object from the given `image_string`.
        
        The `image_string` defines the bitmap of the `Sprite`.  It is a string
        that contains one line for each row in the `Sprite`.  Each line should
        contains the same number of valid color characters.  All whitespace,
        including blank lines, is ignored.  

        Each character in the `image_string` represents one pixel of the
        `Sprite`.  The characters must be either single hex digits representing
        the color (0-9, a-f, A-F) or - (dash) to represent transparency.

        For example, the following string would define a 3x5 letter P, with a transparent center
        of the P:

            f f f
            f - f
            f f f
            f 0 0
            f 0 0
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
        '''Returns the width of the sprite.
        '''
        return len(self.bitmap)

    @property
    def height(self):
        '''Returns the height of the sprite.
        '''
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
        '''In-place crop of the sprite.

        Returns itself, so this function can be chained.
        '''
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
        '''In-place rotation of the sprite.

        `angle` must be a multiple of 90.

        Returns itself, so this function can be chained.
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
        '''In-place horizontal (default) or vertical flip of the sprite.

        Returns itself, so this function can be chained.
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

        Returns itself, so this function can be chained.
        '''
        self.bitmap = self.original_bitmap
        return self
        
class Text(Sprite):
    '''A string of text writable to the framebuffer.

    `Text` is composed of a concatenated string of `Sprite`s, and as such can
    use all the functions available to `Sprite`s.
    '''
    def __init__(self, message, char_spacing=1, font_name='5x7', font_dir=None):
        '''Create a `Text` object from a string.

        `message` is the text string.  Two fonts are supported: '3x5' and
        '5x7'.  Custom fonts can be created by making one sprite file for each
        letter in the font.  The `font_dir` can be changed from the default to
        point to a custom font.

        `char_spacing` is the number of blank pixels that are put between two
        characters in a string.
        '''
        with open(self._font_path(font_dir, font_name, message[0])) as f:
            super().__init__(f.read())
        if len(message) > 1:
            self.__add__(Sprite((('-' * char_spacing) + '\n') * self.height))
            self.__add__(Text(message[1:], char_spacing=char_spacing, font_name=font_name, font_dir=font_dir))

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
    ''' A framebuffer that maps to a chain of LED Matrix RaspberrySTEM Cells.  
    
    The LED Matrices are connected over the SPI bus.  The `FrameBuffer` object
    provides a set of functions for drawing on the framebuffer, and for
    writting the framebuffer to the LED Matrices.  All drawing happens on the
    framebuffer only, until the `show()` function is called.

    The LED Matrices can be mapped to any location in the framebuffer, and can
    also have any rotation (0, 90, 180, 270 deg).  The size of the framebuffer
    is the minimum size rectangle that will include all 8x8 LED Matrices in the
    given matrix_layout.  LED Matrices can be mapped on the same or overlapping
    coordinates in the framebuffer.

    The framebuffer uses Cartesian coordinates: the origin (0,0) is at the
    lower left of the framebuffer.

    The framebuffer uses colors from 0-15 for each pixel, where 0 is off, and
    15 is the highest brightness.
    '''

    def __init__(self, matrix_layout=None, spi_port=0):
        ''' Initialize the `rstem.led_matrix.FrameBuffer`.  
        
        If `matrix_layout` is not given (the default), then the LED Matrix
        chain is autodetected.  To do the autodetection, the LED Matrix chain
        requires that MISO be hooked up, and then the length of the chain can
        be determined.  In this case, the actual layout of the LED Matrices is
        determined from the number of matrices.  The follwing table shows the
        assumed order of the matrices for a given chain length.  The arrows
        show the direction of the input to each matrix in the chain:

            1 matrix:
                --> 1
            2 matrices:
                --> 1 --> 2
            3 matrices:
                --> 1 --> 2 --> 3
            4 matrices:
                --> 1 --> 2 --\\
                              |
                    4 <-- 3 <-/
            5 matrices:
                --> 1 --> 2 --> 3 --> 4 --> 5
            6 matrices:
                --> 1 --> 2 --> 3 --\\
                                    |
                    6 <-- 5 <-- 4 <-/
            7 matrices:
                --> 1 --> 2 --> 3 --> 4 --\\
                                          |
                          7 <-- 6 <-- 5 <-/
            8 matrices:
                --> 1 --> 2 --> 3 --> 4 --\\
                                          |
                    8 <-- 7 <-- 6 <-- 5 <-/
            More than 8 matrices: IOError()

        For arbitrary layouts of matrices, a list of 3-tuples can be provided
        in `matrix_layout`.  There should be one 3-tuple for each LED Matrix in
        the chain, starting with the first matrix.  The 3-tuple should be (x,
        y, rotation), where x/y define the position of the lower left corner
        (after rotation) of the LED Matrix in the Framebuffer.  The rotation is
        a clockwise angle (0, 90, 180, 270) that the LED Matrix is rotated.

        Note that when `matrix_layout` is provided, MISO is not required to be
        hooked up, as it is not used.  This means that the chain will work even
        if the correct number of LED Matrices is not actually hooked up
        (however, not all of the framebuffer data will necessarily be displayed).

        The `spi_port` defines which SPI CE is used: 0 for CE0, 1 for CE1.
        '''
        if not matrix_layout:
            num_matrices = self.detect(spi_port)
            if num_matrices == 0:
                raise IOError('No LED Matrices connected')
            elif num_matrices > 8:
                raise IOError(
                    'More than 8 LED Matrices connected - you must define the matrix_layout')
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
        ''' Draw point (`x`, `y`) in the framebuffer, using the given `color`.

        For convenience, this function accepts a 2-tuple point as `x` if `y` is
        None.  So, for example, both of the following are allowed:

            fb.point(2,3)

        or

            fb.point((2,3))

        The point is drawn in the given `color`.
        '''
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
        '''Erase all pixels in the framebuffer

        `color`, if given, can fill the framebuffer with a specific color.
        '''
        for x in range(self.width):
            for y in range(self.height):
                self.fb[x][y] = color

    def line(self, point_a, point_b, color=0xF):
        '''Draw a line in the framebuffer from `point_a` to `point_b`.

        The line is drawn with the given `color`.
        '''
        # Uses Bresenham's Line Algorithm
        # http://en.wikipedia.org/wiki/Bresenham's_line_algorithm
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
        '''Draws a rectangle in the framebuffer.

        The `origin` is the lower left position of the rectangle.  The
        `dimensions` is a 2-tuple of the width and height.  A width and height
        of 1 would be a 1 point rectangle.

        If `fill` is True, then the interior of the rectanle will be filled.
        Otherwise, only the outside edge of the rectandle will be drawn.  The
        rectangle is drawn in the given `color`.
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
        '''Send the framebuffer to the LED Matrices.

        Sends the current framebuffer to the LED Matrices over the SPI bus,
        according to the layout defined when the framebuffer was initialized.
        This will cause the framebuffer to be displayed on the LED Matrix(es).
        '''
        bitstream = b''
        for xoff, yoff, quarter_clockwise_rotations in reversed(self.matrix_layout):
            forward = range(8)
            backward = list(reversed(forward))
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
        '''Returns the width of the framebuffer.

        The width depends upon the matrix layout.
        '''
        return len(self.fb)

    @property
    def height(self):
        '''Returns the height of the framebuffer.

        The height depends upon the matrix layout.
        '''
        return len(self.fb[0])

    def __str__(self):
        return _color_array_to_str(self.fb, self.height, self.width)

    def draw(self, drawable, origin=(0,0)):
        '''Draw `drawable` into the framebuffer, at given origin.

        `drawable` is either a `Sprite` or `Text` object.
        '''
        xorig, yorig = origin
        bitmap = drawable._bitmap()
        if not bitmap:
            return
        width, height = len(bitmap), len(bitmap[0])
        for x in range(width):
            for y in range(height):
                self.point(xorig + x, yorig + y, bitmap[x][y])

__all__ = ['FrameBuffer', 'Sprite', 'Text']
        
