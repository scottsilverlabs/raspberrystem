#!/usr/bin/python3

import os
import bitstring
import re
import time
from scipy import misc
import numpy
import magic
import led_server     # from the attiny48 controller

SIZE_OF_PIXEL = 4     # 4 bits to represent color
DIM_OF_MATRIX = 8     # 8x8 led matrix elements


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


class LEDMatrix:

    def __init__(self, num_rows=1, num_cols=1, angle=0, zigzag=True):
        """Initializes a matrix of led matrices
        num_rows = number of led matrices set up vertically
        num_cols = number of led matrices set up horizontally
        angle = orientation of x and y coordinates
                - supports angle = 0, 90, 180, and 270
        zigzag = True if matrices set up in zigzag fashion instead of
                    left to right on each rowm
        """
        if num_rows <= 0 or num_cols <= 0:
            raise ValueError("Invalid arguments in LedDraw initialization")
        # create a bitset of all 0's
        self.bitarray = \
            bitstring.BitArray(length=(num_rows*num_cols*SIZE_OF_PIXEL*(DIM_OF_MATRIX**2)))
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.num_matrices = num_rows*num_cols
        self.width = num_cols*DIM_OF_MATRIX
        self.height = num_rows*DIM_OF_MATRIX
        self.angle = angle  # rotation of x y coordinates
        self.zigzag = zigzag
         # sprite that indicates current background
        self.display_sprite = LEDSprite(
            height=num_rows*DIM_OF_MATRIX,
            width=num_cols*DIM_OF_MATRIX
        )
        # initialize spi
        led_server.initSPI(5000000, 0)


    def _convert_to_std_angle(self, x, y):
        """Returns converted coordinate system to standard angle=0 coordinates"""
        if self.angle == 90:
            oldx = x
            x = y
            y = (self.height - 1) - oldx
        elif self.angle == 180:
            x = (self.width - 1) - x
            y = (self.height - 1) - y
        elif self.angle == 270:
            oldy = y
            y = x
            x = (self.width - 1) - oldy
        return (x, y)

    def _in_matrix(self, x, y):
        x, y = self._convert_to_std_angle(x, y)
        return (y >= 0 and y < self.height and x >= 0 and x < self.width)

    def _bitarray_to_bytearray(self):
        """Convert bitarray into an bytearray python type that can be given to led_server"""
        return bytearray(self.bitarray.tobytes())

    def _num_pixels(self):
        return self.height * self.width


    def _point_to_bitpos(self, x, y):
        """Convert the (x,y) coordinates into the bit position in bitarray
        Returns None if point not located on led matrix"""
        # do nothing if x and y out of bound
        if not self._in_matrix(x, y):
            return None

        # convert to standard angle=0 coordinates
        x, y = self._convert_to_std_angle(x, y)

        # figure out what matrix we are dealing with
        mat_col = x/DIM_OF_MATRIX
        mat_row = y/DIM_OF_MATRIX

        # subtract off above matrix row and column so we can treat y relative to matrix row
        y = (y - mat_row*DIM_OF_MATRIX)

        # if on odd matrix row and zigzag enabled, we need to flip x and y coords
        # (this allows us to treat x,y,mat_row,and mat_col as if zigzag == False)
        if mat_row % 2 == 1 and self.zigzag:
            x = (DIM_OF_MATRIX*self.num_cols - 1) - x
            y = (DIM_OF_MATRIX - 1) - y
            mat_col = x/DIM_OF_MATRIX    # update mat_col to new matrix element

        # subtract off left matrix columns so we can treat x relative to matrix element
        x = (x - mat_col*DIM_OF_MATRIX)

        # get bitPos relative to matrix element
        bitPosCol = x*DIM_OF_MATRIX*SIZE_OF_PIXEL
        bitPosColOffset = (DIM_OF_MATRIX - 1 - y)*SIZE_OF_PIXEL
        bitPos = bitPosCol + bitPosColOffset

        # switch matrix element to be flipped version (needed for led_server)
        mat_index = mat_row*self.num_cols + mat_col  # original index
        mat_index = (self.num_matrices - 1) - mat_index  # swapped index

        # convert bitPos to absolute index of entire matrix
        bitPos = mat_index*(DIM_OF_MATRIX**2)*SIZE_OF_PIXEL + bitPos

        # swap nibble (low to high, high to low) (needed for led_server)
        if bitPos % 8 == 0: # beginning of byte
            bitPos += 4
        elif bitPos % 8 == 4: # middle of byte
            bitPos -= 4
        else:
            assert False, "bitPos is not nibble aligned"

        return bitPos


    def show(self):
        """Flushes current display setup to the led matrix"""
        led_server.flush(self._bitarray_to_bytearray())  # give frame buffer to led_server
        # TODO: make more proper debug statement
        if not __debug__:
            for y in range(self.height):
                for x in range(self.width):
                    bitPos = self._point_to_bitpos(x,y)
                    print(self.bitarray[bitPos : bitPos+SIZE_OF_PIXEL].hex),
                print("") # print newline


    def reset(self):
        """Completly clears all display setup and erases the led matrix"""
        self.erase()
        self.show()

    def erase(self):
        self.fill(color=0x0)

    def fill(self, color=0xF):
        """Sets entire display to be filled with given color"""
        old_angle = self.angle
        self.angle = 0    # switch to standard coordinates temporarily
        for x in range(self.width):
            for y in range(self.height):
                self.point(x, y, color)
        self.angle = old_angle

    def point(self, x, y=None, color=0xF):
        """Adds point to bitArray and foreground or background sprite"""
        # If y is not given, then x is a tuple of the point
        color = _convert_color(color)
        if y is None:
            x, y = x
        bitPos = self._point_to_bitpos(x,y)
        if bitPos is None:
            raise Exception("Index out of bounds.")
        if color <= 0xF: # ignore if transparent?
            self.bitarray[bitPos:bitPos+SIZE_OF_PIXEL] = color

        # x, y = self._convert_to_std_angle(x,y)
        # self.display_sprite.set_pixel((x,y), color)

    def _sign(self, n):
        return 1 if n >= 0 else -1


    def line(self, point_a, point_b, color=0xF):
        """Create a line from point_a to point_b"""
        if color < 0x0 or color > 0xF:
            raise ValueError("Invalid color")

        x_diff = point_a[0] - point_b[0]
        y_diff = point_a[1] - point_b[1]
        step = self._sign(x_diff) * self._sign(y_diff)
        width = abs(x_diff) + 1
        height = abs(y_diff) + 1
        if (width > height):
            start_point = point_a if x_diff < 0 else point_b
            start_x, start_y = start_point
            for x_offset in range(width):
                self.point(
                    start_x + x_offset,
                    start_y + step*(x_offset*height/width),
                    color=color
                )
        else:
            start_point = point_a if y_diff < 0 else point_b
            start_x, start_y = start_point
            for y_offset in range(height):
                self.point(
                    start_x + step*(y_offset*width/height),
                    start_y + y_offset,
                    color=color
                )


    def rect(self, start, dimensions, color=0xF):
        """Creates a rectangle from start point using given dimensions"""
        x, y = start
        width, height = dimensions
        self.line((x, y), (x, y + height), color)
        self.line((x, y + height), (x + width, y + height), color)
        self.line((x + width, y + height), (x + width, y), color)
        self.line((x + width, y), (x, y), color)

    def text(self, text, x=0, y=0, scrolling=False):
        """Sets given string to be displayed on LED Matrix
            - returns the LEDMessage sprite object used to create text
        """
        if type(text) == str:
            text = LEDMessage(text)
        elif type(text) != LEDMessage and type(text) != LEDSprite:
            raise ValueError("Invalid text")
        self.sprite(text, (x,y))
        # TODO: remove scrolling, let it be a user program
        if scrolling:
            while 1:
                self.erase()
                if (x + text.width) < 0: # reset x
                    x = self.width
                self.sprite(text, (x,y))
                self.show()
                x -= 1
        return text


    def sprite(self, sprite, (x,y)=(0,0)):
        """Sets given sprite with top left corner at given position"""
        x_offset = x
        y_offset = y
        for y, line in enumerate(sprite.bitmap):
            y = y + y_offset
            if y < 0:
                continue
            # stop if we go lower than physical display
            if not self._in_matrix(0,y):
                break
            for x, color in enumerate(line):
                x = x + x_offset
                if x < 0:
                    continue
                # stop if we go too far to the right of physical display
                if not self._in_matrix(x,0):
                    break
                self.point(
                    x,
                    y,
                    color=color,
                    background=background
                )



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

    def set_pixel(self, (x,y), color=0xF):
        """Sets given color to given x and y coordinate in sprite
            - color can be a int or string of hex value
            - return None if coordinate is not valid
        """
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
