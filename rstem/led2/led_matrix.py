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
        self.angle = angle  # rotation of x y coordinates
        self.zigzag = zigzag
         # sprite that indicates current background
        self.bgsprite = LEDSprite(
            height=num_rows*DIM_OF_MATRIX,
            width=num_cols*DIM_OF_MATRIX
        )
        self.fgsprite = LEDSprite(
            height=num_rows*DIM_OF_MATRIX,
            width=num_cols*DIM_OF_MATRIX,
            color='-'
        )
        
        # initialize spi
        led_server.initSPI()
        
    def _get_width(self):
        return self.num_cols*DIM_OF_MATRIX
        
    def _get_height(self):
        return self.num_rows*DIM_OF_MATRIX
        
    def _in_matrix(self, x, y):
        return (y >= 0 and y < self._get_height() and x >= 0 and x < self._get_width())
        
    def _bitarray_to_bytearray(self):
        """Convert bitarray into an bytearray python type that can be given to led_server"""     
        return bytearray(self.bitarray.tobytes())
        
    def _num_pixels(self):
        return self._get_height() * self._get_width()
          
    def _point_to_bitpos(self, x, y):
        """Convert the (x,y) coordinates into the bit position in bitarray
        Returns None if point not located on led matrix"""
        # convert coordinate system to standard angle=0 coordinates
        if self.angle == 90:
            oldx = x
            x = y
            y = (self._get_height() - 1) - oldx
        elif self.angle == 180:
            x = (self._get_width() - 1) - x
            y = (self._get_height() - 1) - y
        elif self.angle == 270:
            oldy = y
            y = x
            x = (self._get_width() - 1) - oldy
        
        # do nothing if x and y out of bound
        if not self._in_matrix(x, y):
            return None
           
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
        led_server.flush(self._bitarray_to_bytearray())  # give frame buffer to led_server
        if not __debug__:
            for y in range(self._get_height()):
                for x in range(self._get_width()):
                    bitPos = self._point_to_bitpos(x,y)
                    print(self.bitarray[bitPos : bitPos+SIZE_OF_PIXEL].hex),
                print("") # print newline
        
    def erase(self):
        self.clear_background()
        self.clear_foreground()
#        self.bitarray = \
#            bitstring.BitArray(length=(self.num_matrices*SIZE_OF_PIXEL*DIM_OF_MATRIX**2))
        self.show()
        
    def fill(self, color=0x0, background=False):
        old_angle = self.angle
        self.angle = 0    # switch to standard coordinates temporarily
        for x in range(self._get_width()):
            for y in range(self._get_height()):
                self.point(x, y, color, background)
        self.angle = old_angle
        
    def point(self, x, y, color=0xF, background=False):
        """Adds point to bitArray and foreground or background sprite"""
        if color < 0x0 or color > 0xF:
            raise ValueError("Invalid Color, must be between 0x0-0xF")
            
        if background:
            self.bgsprite.set_pixel(x, y, color)
             # if foreground not transparent don't display it
            if self.fgsprite.get_pixel(x, y) != '-':
                return
        else:
            self.fgsprite.set_pixel(x, y, color)
            
        # set to display color
        bitPos = self._point_to_bitpos(x, y)
        if bitPos is None: # out of bound
            return          
        self.bitarray[bitPos:bitPos+SIZE_OF_PIXEL] = color  # set 4 bits
            
            
    def _sign(self, n):
        return 1 if n >= 0 else -1
            
            
    def line(self, point_a, point_b, color=0xF, background=False):
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
                    color=color,
                    background=background
                )
        else:
            start_point = point_a if y_diff < 0 else point_b
            start_x, start_y = start_point
            for y_offset in range(height):
                self.point(
                    start_x + step*(y_offset*width/height),
                    start_y + y_offset,
                    color=color,
                    background=background
                )
    
    
    def rect(self, start, dimensions, color=0xF, background=False):
        x, y = start
        width, height = dimensions
        self.line((x, y), (x, y + height), color, background)
        self.line((x, y + height), (x + width, y + height), color, background)
        self.line((x + width, y + height), (x + width, y), color, background)
        self.line((x + width, y), (x, y), color, background)
        
    def set_sprite(self, sprite, x=0, y=0, background=False):
        """Sets given sprite with top left corner at given position"""
        x_offset = x
        y_offset = y
        for y, line in enumerate(sprite.bitmap):
            for x, pixel in enumerate(line):
                if pixel != '-': # don't do anything if transparent
                    self.point(
                        x + x_offset,
                        y + y_offset,
                        color=int(pixel, 16),
                        background=background
                    )
    
    def clear_sprite(self, sprite, x=0, y=0, background=False):
        """Clears given sprite at given position
            - subsitutes the pixels the sprite was covering with the background
            - note assumes the sprite was already there
                - this function will clear the foreground the shape of the sprite
        """
        x_offset = x
        y_offset = y
        for y, line in enumerate(sprite.bitmap):
            for x, pixel in enumerate(line):
                if pixel != '-': # don't do anything if transparent
                    x = x + x_offset
                    y = y + y_offset
                    if background:
                        # if clearing background pixel set color to 0
                        # (this also sets background sprite to 0)
                        self.point(x, y, 0, background=True)
                    else:
                        # else set background to be displayed
                        self.point(x, y, int(self.bgsprite.get_pixel(x, y), 16))
                        # remove pixel from foreground by setting it to transparent
                        self.fgsprite.set_pixel(x, y, '-')

    def update_sprite(self, sprite, before_pos, after_pos):
        self.clear_sprite(sprite, *before_pos)
        self.set_sprite(sprite, *after_pos)
        
        
    def update_background(self, sprite=None, x=0, y=0):
        """Allows you to update the position of the background or set a new background"""
        if sprite is None:
            self.set_sprite(self.bgsprite, x, y, background=True)
        else:
            self.set_sprite(sprite, x, y, background=True)
            
    def clear_background(self):
        """Removes the background, doesn't touch foreground"""
        self.clear_sprite(self.bgsprite, background=True)
        
    def clear_foreground(self):
        """Remove the foreground, doesn't touch the background"""
        self.clear_sprite(self.fgsprite)

            
class LEDSprite:
    """Allows the creation of a LED Sprite that is defined in a text file.
        - The text file must only contain hex numbers 0-9, a-f, A-F, or - (dash)
        - The hex number indicates pixel color and "-" indicates a transparent pixel
    """
    def __init__(self, filename=None, height=0, width=0, color='0'):
        self.filename = filename
        bitmap = []
        bitmap_width = 0  # keep track of width and height
        bitmap_height = 0
        if filename is not None:
            # get file type
            mime = magic.Magic(mime=True)
            filetype = mime.from_file(filename)
            image_file = (filetype.find("image") != -1)
            txt_file = (filetype == "text/plain")
            if image_file:
                if height <= 0 or width <= 0:
                    raise ValueError("Must provide a height and width for image")
                # pixelize and resize image with scipy
                image = misc.imread(filename, flatten=1)
                con_image = misc.imresize(image, (width, height), interp='cubic')
                bitmap = [[hex(15 - pixel*15/255)[2] for pixel in line] for line in con_image]
            elif txt_file:
                f = open(filename, 'r')
                for line in f:
                    if not re.match(r'^[0-9a-fA-F\s-]+$', line):
                        raise ValueError("Bitmap file contains invalid characters")
                    # Determine if widths are consistent
                    leds = line.split()
                    if bitmap_width != 0:
                        if len(leds) != bitmap_width:
                            raise ValueError("Bitmap has different widths")
                    else:
                        bitmap_width = len(leds)
                    bitmap.append(leds)
                    bitmap_height += 1
                f.close()
            else:
                raise ValueError("Unsupported filetype")
        # set custom height if given and not filename
        if height > 0 and width > 0 and filename is None:
            bitmap = [[color for i in range(width)] for j in range(height)]
            bitmap_height = height
            bitmap_width = width
            
        self.bitmap = bitmap
        self.height = bitmap_height
        self.width = bitmap_width
        
    def set_pixel(self, x, y, color=0xF):
        """Sets given color to given x and y coordinate in sprite
            - color can be a int or string of hex value
            - return None if coordinate is not valid
        """
        if x >= self.width or y >= self.height or x < 0 or y < 0:
            return None
        if type(color) is int:
            if color < 0x0 or color > 0xF:
                raise ValueError("Invalid color")
            self.bitmap[y][x] = hex(color)[2]
        elif type(color) is str:
            if not re.match(r'^[0-9a-fA-F-]$', color):
                raise ValueError("Not a valid color")
            self.bitmap[y][x] = color
        else:
            raise ValueError("Invalid color type")
        return 1
            
    def get_pixel(self, x, y):
        """Returns string of color at given position or None
        """
        if x >= self.width or y >= self.height or x < 0 or y < 0:
            return None
        return self.bitmap[y][x]
        
        
    def save_to_file(self, filename):
        pass
        # TODO: ???
            
            
