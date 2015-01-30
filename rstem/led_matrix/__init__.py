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

# global variables for use
BITS_PER_PIXEL = 4     # 4 bits to represent color
DIM_OF_MATRIX = 8     # 8x8 led matrix elements
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


def _convert_to_std_coords(x, y):
    """Converts given math coordinates to standard programming coordinates
    @param x: x coordinate in math coordinates
    @param y: y coordinate in math coordinates
    @rtype: tuple
    @return: (x,y) coordinates in standard programming coordinates"""
    return x, (height - 1 - y)


def text(text, origin=(0, 0), crop_origin=(0, 0), crop_dimensions=None, font_name="small", font_path=None):
    """Sets given string to be displayed on the led matrix
        
    Example:
        >>> text("Hello World", (0,0), (0,1), (0,5))
        >>> show()
        Displays only part of the first vertical line in 'H'
        
    @param origin, crop_origin, crop_dimensions: See L{sprite}
        
    @param text: text to display
    @param text: string or L{LEDText}
    @param font_name: Font folder (or .font) file to use as font face
    @type font_name: string
    @param font_path: Directory to use to look for fonts. If None it will used default directory in dist-packages
    @type font_path: string
    
    @returns: LEDText sprite object used to create text
    @rtype: L{LEDText}
    """
    if type(text) == str:
        text = LEDText(text, font_name=font_name, font_path=font_path)
    elif type(text) != LEDText and type(text) != LEDSprite:
        raise ValueError("Invalid text")
    sprite(text, origin, crop_origin, crop_dimensions)
    return text


def sprite(sprite, origin=(0,0), crop_origin=(0,0), crop_dimensions=None):
    """Sets given sprite into the framebuffer.
    
    @param origin: Bottom left position to diplay text (top left if math_coords == False)
    @type origin: (x,y) tuple
    @param crop_origin: Position to crop into the sprite relative to the origin
    @type crop_origin: (x,y) tuple
    @param crop_dimensions: x and y distance from the crop_origin to display
        - Keep at None to not crop and display sprite all the way to top right corner (bottom right for math_coords == False)
    @type crop_dimensions: (x,y) tuple
    """
    if type(sprite) == str:
        sprite = LEDSprite(sprite)
    elif type(sprite) != LEDText and type(sprite) != LEDSprite:
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
        
class LEDSprite(object):
    """Allows the creation of a LED Sprite that is defined in a text file.
    @note: The text file must only contain hex numbers 0-9, a-f, A-F, or - (dash)
    @note: The hex number indicates pixel color and "-" indicates a transparent pixel
    """
    def __init__(self, filename=None, height=0, width=0, color=0x0):
        """Creates a L{LEDSprite} object from the given .spr file or image file or creates an empty sprite of given
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
        bitmap = []
        bitmap_width = 0  # keep track of width and height
        bitmap_height = 0
        if filename is not None:
            filename = filename.strip()
            self.filename = filename    
            # get filetype
            proc = subprocess.Popen("file " + str(filename), shell=True, stdout=subprocess.PIPE)
            output, errors = proc.communicate()
            if type(output) == bytes:  # convert from byte to a string (happens if using python3)
                output = output.decode() 
            if errors is not None or (output.find("ERROR") != -1):
                raise IOError(output)
                
            if output.find("text") != -1 or output.find("FORTRAN") != -1:  # file is a text file
                if filename[-4:] != ".spr":
                    raise ValueError("Filename must have '.spr' extension.")
                f = open(filename, 'r')
                for line in f:
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
                
            elif output.find("image") != -1:  # file is an image file
                import scipy.misc, numpy, sys
                if sys.version_info[0] > 2:
                    raise ValueError("As of now, only python 2 supports images to sprites.")
                # if no height or width given try to fill as much of the display
                # with the image without stretching it
                if height <= 0 or width <= 0:
                    from PIL import Image
                    im = Image.open(filename)
                    im_width, im_height = im.size
                    bitmap_height = min(height, im_height)
                    bitmap_width = min(width, bitmap_height * (im_width / im_height))
                else:
                    bitmap_height = height
                    bitmap_width = width
                # pixelize and resize image with scipy
                image = scipy.misc.imread(filename, flatten=True)
                con_image = scipy.misc.imresize(image, (bitmap_width, bitmap_height), interp='cubic')
                con_image = numpy.transpose(con_image)  # convert from column-wise to row-wise
                con_image = numpy.fliplr(con_image)  # re-orient the image
                con_image = numpy.rot90(con_image, k=1)
                bitmap = [[int(pixel*16/255) for pixel in line] for line in con_image]  # convert to bitmap
            else:
                raise IOError("Unsupported filetype")
        else:
            # create an empty sprite of given height and width
            bitmap = [[color for i in range(width)] for j in range(height)]
            bitmap_height = height
            bitmap_width = width

        self.bitmap = bitmap
        # self.height = bitmap_height
        # self.width = bitmap_width

    @property
    def width(self):
        return len(self.bitmap[0])

    @property
    def height(self):
        return len(self.bitmap)

    def append(self, sprite):
        """Appends given sprite to the right of itself.
        
        @param sprite: sprite to append
        @type sprite: L{LEDSprite}
        @note: height of given sprite must be <= to itself otherwise will be truncated
        """
        for i, line in enumerate(self.bitmap):
            if i >= sprite.height:
                # fill in with transparent pixels
                tran_line = [0x10 for j in range(sprite.width)]
                self.bitmap[i] = sum([line, tran_line], [])
            else:
                self.bitmap[i] = sum([line, sprite.bitmap[i]], [])
        # update size
        # self.width += sprite.width

    def set_pixel(self, point, color=0xF):
        """Sets given color to given x and y coordinate in sprite

        @param point: point relative to sprite to set point
        @type point: (x,y)
        @param color: Color to display at point
        @type color: int or string (0-F or 16 or '-' for transparent)
        
        @return: None if coordinate is not valid
        """
        x, y = point
        if x >= self.width or y >= self.height or x < 0 or y < 0:
            return None
        self.bitmap[y][x] = _convert_color(color)

    def get_pixel(self, x, y):
        """
        @rtype: int
        @returns: int of color at given origin or None
        """
        if x >= self.width or y >= self.height or x < 0 or y < 0:
            return None
        return self.bitmap[y][x]

    
    def save_to_file(self, filename):
        """Saves sprite bitmap to given .spr file. 
        
        @param filename: relative filename path
        @type filename: string
        @note: It will truncate filename if it already exists.
        """
        filename = filename.strip()
        if filename[-4:] != ".spr":
            raise ValueError("Filename must have '.spr' extension.")
        f = open(filename, 'w')
        for line in self.bitmap:
            for pixel in line:
                if pixel > 15:
                    f.write("- ")
                else:
                    f.write(hex(pixel)[2] + " ")
            f.write("\n")
        f.close()
        
    def rotate(self, angle=90):
        """Rotates sprite at 90 degree intervals. 
        
        @returns: self
        @rtype: L{LEDSprite}
        
        @param angle: angle to rotate self in an interval of 90 degrees
        @type angle: int
        
        @returns: self
        @rtype: L{LEDSprite}
        @raises ValueError: If angle is not multiple of 90
        @note: If no angle given, will rotate sprite 90 degrees.
        """
        if angle % 90 != 0:
            raise ValueError("Angle must be a multiple of 90.")
            
        angle = angle % 360    
        if angle == 90:
            bitmap = []
            for i in range(self.width):
                bitmap.append([row[i] for row in reversed(self.bitmap)])
            self.bitmap = bitmap
            # swap height and width
            # temp = self.width
            # self.width = self.height
            # self.height = temp
            
        elif angle == 180:
            self.bitmap.reverse()
            for row in self.bitmap:
                row.reverse()
                
        elif angle == 270:
            bitmap = []
            for i in range(self.width-1,-1,-1):
                bitmap.append([row[i] for row in self.bitmap])
            self.bitmap = bitmap
            # swap height and width
            # temp = self.width
            # self.width = self.height
            # self.height = temp
        return self
        
    def rotated(self, angle=90):
        """Same as L{rotate} only it returns a copy of the rotated sprite
        and does not affect the original.
        @returns: Rotated sprite
        @rtype: L{LEDSprite}
        """
        sprite_copy = copy.deepcopy(self)
        sprite_copy.rotate(angle)
        return sprite_copy
        
    def copy(self):
        """Copies sprite
        @returns: A copy of sprite without affecting original sprite
        @rtype: L{LEDSprite}
        """
        return copy.deepcopy(self)
        
    def invert(self):
        """Inverts the sprite.
        @returns: self
        @rtype: L{LEDSprite}
        """
        for y, line in enumerate(self.bitmap):
            for x, pixel in enumerate(line):
                if pixel < 16:
                    self.bitmap[y][x] = 15 - pixel
                    
    def inverted(self):
        """Same as L{invert} only it returns a copy of the inverted sprite
        and does not affect the original.
        @returns: Inverted sprite
        @rtype: L{LEDSprite}
        """
        sprite_copy = copy.deepcopy(self)
        sprite_copy.invert()
        return sprite_copy
        
    def flip_horizontal(self):
        """Flips the sprite horizontally.
        @returns: self
        @rtype: L{LEDSprite}
        """
        self.bitmap.reverse()
        return self
        
    def flipped_horizontal(self):
        """Same as L{flip_horizontal} only it returns a copy of the flipped sprite
        and does not affect the original.
        @returns: sprite flipped horizontally
        @rtype: L{LEDSprite}
        """
        sprite_copy = copy.deepcopy(self)
        sprite_copy.flip_horizontal()
        return sprite_copy
        
        
    def flip_vertical(self):
        """Flips the sprite vertically.
        @returns: self
        @rtype: L{LEDSprite}
        """
        for line in self.bitmap:
            line.reverse()
        return self
        
    def flipped_vertical(self):
        """Same as L{flip_vertical} only it returns a copy of the flipped sprite
        and does not affect the original.
        @returns: sprite flipped vertically
        @rtype: L{LEDSprite}
        """
        sprite_copy = copy.deepcopy(self)
        sprite_copy.flip_vertical()
        return sprite_copy


def _char_to_sprite(char, font_path):
    """Converts given character to a sprite.
    
    @param char: character to convert (must be of length == 1)
    @type char: string
    @param font_path: Relative location of font face to use.
    @type font_path: string
    @rtype: L{LEDSprite}
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
        return LEDSprite(font_path)
    else:
        return LEDSprite(os.path.join(orig_font_path, "unknown.spr"))
        
        

class LEDText(LEDSprite):
    """A L{LEDSprite} object of a piece of text."""
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
            super(LEDSprite, self).__init__()
            return

        # start with first character as intial sprite object
        init_sprite = _char_to_sprite(message[0], font_path)
        # get general height and width of characters

        if len(message) > 1:
            # append other characters to initial sprite
            for char in message[1:]:
                # add character spacing
                init_sprite.append(LEDSprite(height=init_sprite.height, width=char_spacing, color=0x10))
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

    @property
    def width(self):
        return 8

    @property
    def height(self):
        return 8


__all__ = ['FrameBuffer']
        
