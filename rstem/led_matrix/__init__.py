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
from itertools import islice
import led_driver     # c extension that controls led matrices and contains framebuffer
import copy
import subprocess

# global variables for use
BITS_PER_PIXEL = 4     # 4 bits to represent color
DIM_OF_MATRIX = 8     # 8x8 led matrix elements
initialized = False   # flag to indicate if LED has been initialized
spi_initialized = False  # flag to indicate if SPI bus as been initialized
container_width = 0    # indicates the maximum width and height of the LEDContainer
container_height = 0
container_math_coords = True


def _init_check():
    """Checks that init_matrices has been called and throws an error if not"""
    global initialized
    if not initialized:
        raise RuntimeError("Matrices must be initialized first.")
    

def _valid_color(color):
    """Checks if given color is number between 0-16 if an int or 0-f, or - if string"""
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
    elif type(color) == str:
        if color == '-':
            return 0x10
        return int(color, 16)
    raise RuntimeError("Invalid color")
    
def _convert_to_std_coords(x, y):
    """Converts given math coordinates to standard programming coordinates"""
    return (x, (container_height - 1 - y))
    
def width():
    return container_width
    
def height():
    return container_height
    
def display_on_terminal():
    led_driver.display_on_terminal()

def init_matrices(mat_list=[(0,0,0)], math_coords=True, spi_speed=500000, spi_port=0):
    """Create a chain of led matrices set at particular offsets into the frame buffer
    The order of the led matrices in the list indicate the order they are
    physically hooked up with the first one connected to Pi.
    mat_list = list of tuple that contains led matrix and offset
        ex: [(0,0,0),(7,0,90)]
        """
    global initialized
    global container_width
    global container_height
    global container_math_coords
    if initialized: # free previous memory before attempting to do it again
        cleanup()
                
    container_width = max([matrix[0] for matrix in mat_list]) + DIM_OF_MATRIX
    container_height = max([matrix[1] for matrix in mat_list]) + DIM_OF_MATRIX
    container_math_coords = math_coords
    if container_math_coords:
        for i in range(len(mat_list)):
            # convert y's to be standard programming coordinates
            # and also move origin from bottom left to top left of matrix
            if len(mat_list[i]) > 2:
                mat_list[i] = (mat_list[i][0], (container_height-1 - mat_list[i][1]) - (DIM_OF_MATRIX-1), mat_list[i][2])
            else:
                mat_list[i] = (mat_list[i][0], (container_height-1 - mat_list[i][1]) - (DIM_OF_MATRIX-1))
    led_driver.init_matrices(mat_list, len(mat_list), \
        container_width, container_height) # flatten out tuple
        
    # initialize spi bus
    global spi_initialized
    if not spi_initialized:
        led_driver.init_SPI(spi_speed, spi_port)
        spi_initialized = True
    
    initialized = True
    
def init_grid(num_rows=None, num_cols=None, angle=0, math_coords=True, spi_speed=500000, spi_port=0):
    """Initiallizes led matrices in a grid pattern with the given number
    or rows and columns.
    zigzag=True means the ledmatrices have been placed in a zigzag fashion.
    angle=0, 90, 180, or 270 to represent how the coordinate system should be
            represented in the grid
            (num_row and num_cols are representative of after the angle has been defined)
    """
    # initialize spi bus right away because we need it for led_driver.detect()
    global spi_initialized
    if not spi_initialized:
        led_driver.init_SPI(spi_speed, spi_port)
        spi_initialized = True
    
    # num_rows, and num_cols are before rotation
    # auto detect number of columns if none given
    num_matrices = led_driver.detect()
    if num_cols is None:
        if num_rows is None:
            # if number of rows not given assume max of 4 columns per row
            for cols in reversed(range(5)):  # should never hit zero
                rows = float(num_matrices)/cols
                if rows.is_integer():
                    num_rows = int(rows)
                    num_cols = cols
                    break
        else:
            num_cols = num_matrices/num_rows
    elif num_rows is None:
        raise ValueError("If you are providing num_cols you must also provide num_rows.")
    
    if num_cols*num_rows != num_matrices:  # safety check
        raise ValueError("Invalid number of rows and columns")
    
    if angle % 90 != 0:
        raise ValueError("Angle must be a multiple of 90.")
    angle = angle % 360
    
    mat_list = []
    if angle == 0:
        for row in range(num_rows): # increment through rows downward
            if row % 2 == 1:
                for column in range(num_cols-1,-1,-1):  # if odd increment right to left
                    mat_list.append((column*DIM_OF_MATRIX, row*DIM_OF_MATRIX, 180))  # upside-down
            else:
                for column in range(num_cols): # if even, increment left to right
                    mat_list.append((column*DIM_OF_MATRIX, row*DIM_OF_MATRIX, 0))  # right side up
    elif angle == 90: # 90 degrees clockwise
        for row in range(num_rows): 
            if row % 2 == 1:
                for column in range(num_cols-1,-1,-1): # if odd, increment downward
                    mat_list.append(((num_rows-row - 1)*DIM_OF_MATRIX, column*DIM_OF_MATRIX, 270)) # 180 + 90
            else:
                for column in range(num_cols): # if even, increment upwards
                    mat_list.append(((num_rows-row - 1)*DIM_OF_MATRIX, column*DIM_OF_MATRIX, 90))  # 0 + 90
    elif angle == 180:
        for row in range(num_rows-1,-1,-1): # increment through rows upwards
            if row % 2 == 1:
                for column in range(num_cols-1,-1,-1):  # if odd increment right to left
                    mat_list.append((column*DIM_OF_MATRIX, row*DIM_OF_MATRIX, 180)) # 180 + 180
            else:
                for column in range(num_cols): # if even increment left to right
                    mat_list.append((column*DIM_OF_MATRIX, row*DIM_OF_MATRIX, 0)) # 0 + 180
    elif angle == 270: # 90 degrees counter-clockwise
        for row in range(num_rows): # increment columns right to left
            if row % 2 == 1:
                for column in range(num_cols-1,-1,-1): # if odd increment through rows upwards
                    mat_list.append((row*DIM_OF_MATRIX, (num_cols - 1- column)*DIM_OF_MATRIX, 90)) # 180 - 90
            else:
                for column in range(num_cols): # increment through rows downwards
                    mat_list.append((row*DIM_OF_MATRIX, (num_cols - 1 - column)*DIM_OF_MATRIX, 270)) # 0 - 90 = 270
                  
    global container_math_coords
    init_matrices(mat_list, math_coords=False, spi_speed=spi_speed, spi_port=spi_port)
    container_math_coords = math_coords

def show():
    """Tells the led_driver to send framebuffer to SPI port.    
    Refreshes the display using current framebuffer.
    """
    _init_check()
    led_driver.flush()
    return 1

def cleanup():
    """Unintializes matrices and frees all memory. 
    Should be called at the end of a program to avoid memory leaks.
    Also, clears the display.
    """
    global initialized
    if initialized:
        led_driver.fill(0x0)
        led_driver.flush()
        led_driver.shutdown_matrices()
        initialized = False
        spi_initialized = False

def fill(color=0xF):
    """Fills the framebuffer with the given color.
    (Full brightness if no color is given).
    """
    _init_check()
    led_driver.fill(_convert_color(color))

    
def erase():
    fill(0)

def point(x, y=None, color=0xF):
    """Sends point to the framebuffer.
    Note: will not display the point until show() is called.
    """
    _init_check()
    color = _convert_color(color)
    if color < 16:   # don't do anything if transparent
        global container_width
        global container_height
        # If y is not given, then x is a tuple of the point
        if y is None and type(x) is tuple:
            x, y = x
        if x < 0 or x >= container_width or y < 0 or y >= container_height:
            return
        if container_math_coords:
            x, y = _convert_to_std_coords(x, y)
        led_driver.point(int(x), int(y), color)
        return 1

def rect(origin, dimensions, fill=True, color=0xF):
    """Creates a rectangle from start point using given dimensions"""
    x, y = origin
    width, height = dimensions

    if fill:
        for x_offset in range(width):
            line((x + x_offset, y), (x + x_offset, y + height - 1), color)
    else:
        line((x, y), (x, y + height - 1), color)
        line((x, y + height - 1), (x + width - 1, y + height - 1), color)
        line((x + width - 1, y + height - 1), (x + width - 1, y), color)
        line((x + width - 1, y), (x, y), color)
    


def _sign(n):
    return 1 if n >= 0 else -1

def line(point_a, point_b, color=0xF):
    """Create a line from point_a to point_b.
    Uses Bresenham's Line Algorithm (http://en.wikipedia.org/wiki/Bresenham's_line_algorithm)
    """
    x1, y1 = point_a
    x2, y2 = point_b
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    while True:
        point(x1, y1, color)
        if ((x1 == x2 and y1 == y2) or x1 >= container_width or y1 >= container_height):
            break
        e2 = 2*err
        if (e2 > -dy):
            err -= dy
            x1 += sx
        if (e2 < dx):
            err += dx
            y1 += sy
            
def _line_fast(point_a, point_b, color=0xF):
    """A faster c implementation of line. Use if you need the speed."""
    if container_math_coords:
        point_a = _convert_to_std_coords(*point_a)
        point_b = _convert_to_std_coords(*point_b)
    led_driver.line(point_a[0], point_a[1], point_b[0], point_b[1], _convert_color(color))


def text(text, origin=(0,0), crop_origin=(0,0), crop_dimensions=None, font_name="small", font_path=None):
    """Sets given string to be displayed on LED Matrix
        - returns the LEDText sprite object used to create text
    """
    if type(text) == str:
        text = LEDText(text, font_name=font_name, font_path=font_path)
    elif type(text) != LEDText and type(text) != LEDSprite:
        raise ValueError("Invalid text")
    sprite(text, origin, crop_origin, crop_dimensions)
    return text


def sprite(sprite, origin=(0,0), crop_origin=(0,0), crop_dimensions=None):
    """Sets given sprite with top left corner at given origin
        origin = the (x,y) coordinates to start displaying the sprite 
            (bottom left for math_coords, top left for programming coords)
        crop_origin = the offset into the sprite that should actually be displayed
                Note: crop_origin is relative to origin
        crop_dimensions = the number of pixels (x, y) inside the sprite to display (None for no crop)
    """
    if type(sprite) == str:
        sprite = LEDSprite(sprite)
    elif type(sprite) != LEDText and type(sprite) != LEDSprite:
        raise ValueError("Invalid sprite")
    
    _init_check()
    global container_width
    global container_height
    
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
    
    if x_start >= container_width or y_start >= container_height:
        return
        
    # set up end position
    x_end = min(x_pos + x_crop + x_crop_dim, container_width, x_pos + sprite.width)
    y_end = min(y_pos + y_crop + y_crop_dim, container_height, y_pos + sprite.height)
    
    
    # iterate through sprite and set points to led_driver
    y = y_start
    while y < y_end:
        x = x_start
        while x < x_end:
            x_sprite = x - x_start + x_crop
            y_sprite = y - y_start + y_crop
            if container_math_coords:
                y_sprite = sprite.height - 1 - y_sprite
            point((x, y), color=sprite.bitmap[y_sprite][x_sprite])
            x += 1
        y += 1
        
def frame(numpy_bitmap):
    """Sends the entire frame (represented in a bitmap) to the led matrix.
    Note: bitmap dimensions must be the same as the dimensions of the container (non rotated).
    """
    led_driver.frame(numpy_bitmap)


class LEDSprite(object):
    """Allows the creation of a LED Sprite that is defined in a text file.
        - The text file must only contain hex numbers 0-9, a-f, A-F, or - (dash)
        - The hex number indicates pixel color and "-" indicates a transparent pixel
    """
    def __init__(self, filename=None, height=0, width=0, color=0x0):
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
                
            if output.find("text") != -1:  # file is a text file
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
                    bitmap_height = min(container_height, im_height)
                    bitmap_width = min(container_width, bitmap_height * (im_width / im_height))
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
        """Returns int of color at given origin or None
        """
        if x >= self.width or y >= self.height or x < 0 or y < 0:
            return None
        return self.bitmap[y][x]

    
    def save_to_file(self, filename):
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
        If no angle given, will rotate sprite 90 degrees.
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
            temp = self.width
            self.width = self.height
            self.height = temp
            
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
            temp = self.width
            self.width = self.height
            self.height = temp
        
    def rotated(self, angle=90):
        """Returns a rotated LEDSprite of self. Does not change self."""
        sprite_copy = copy.deepcopy(self)
        sprite_copy.rotate(angle)
        return sprite_copy


def _char_to_sprite(char, font_path):
    """Returns the LEDSprite object of given character."""
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

    def __init__(self, message, char_spacing=1, font_name="small", font_path=None):
        """Creates a text sprite of the given string
            - This object can be used the same way a sprite is used
            char_spacing = number pixels between characters
            font_path = location of folder where font sprites are located
                        leave as None to use default system fonts
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
            return None
        # start with first character as intial sprite object
        init_sprite = _char_to_sprite(message[0], font_path)
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
                # now add next character
                sprite = _char_to_sprite(char, font_path)
                if sprite.height != height:
                    raise ValueError("Height of character sprites must all be the same.")
                # append
                init_sprite.append(sprite)

        self.bitmap = init_sprite.bitmap
        self.height = init_sprite.height
        self.width = init_sprite.width
        
        
# run demo program if run by itself
def _main():
    init_matrices()
    while 1:
        for x in range(8):
            for y in range(8):
                point(x, y)
                show()
                time.sleep(0.5);
                erase()

if __name__ == "__main__":
    _main()

