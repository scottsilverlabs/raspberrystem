#!/usr/bin/python3

import os
import bitstring
import re
import time
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
        self.bitarray = \
            bitstring.BitArray(length=(self.num_matrices*SIZE_OF_PIXEL*DIM_OF_MATRIX**2))
        self.show()
        
    def fill(self, color=0x0):
        old_angle = self.angle
        self.angle = 0    # switch to standard coordinates temporarily
        for x in range(self._get_width()):
            for y in range(self._get_height()):
                self.point(x, y, color)
        self.angle = old_angle
        
    def point(self, x, y, color=0xF):
        """Adds point to bitArray"""
        if color < 0x0 or color > 0xF:
            raise ValueError("Invalid Color")
            return
        bitPos = self._point_to_bitpos(x, y)
        if bitPos is not None:
            self.bitarray[bitPos:bitPos+4] = color  # set 4 bits
            
            
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
                    color=color)
        else:
            start_point = point_a if y_diff < 0 else point_b
            start_x, start_y = start_point
            for y_offset in range(height):
                self.point(
                    start_x + step*(y_offset*width/height),
                    start_y + y_offset,
                    color=color)
    
    
    def rect(self, start, dimensions, color=0xF):
        x, y = start
        width, height = dimensions
        self.line((x, y), (x, y + height), color=color)
        self.line((x, y + height), (x + width, y + height), color=color)
        self.line((x + width, y + height), (x + width, y), color=color)
        self.line((x + width, y), (x, y), color=color)
        
    def sprite(self, sprite, x_offset=0, y_offset=0):
        """Sets given sprite with top left corner at given position"""
        for y, line in enumerate(sprite.bitmap):
            for x, pixel in enumerate(line):
                if pixel != '-':
                    self.point(x + x_offset, y + y_offset, color=int(pixel, 16))


            
class LEDSprite:
    """Allows the creation of a LED Bitmap that is defined in a text file.
        - The text file must only contain hex numbers 0-9, a-f, A-F, or - (dash)
        - The hex number indicates pixel color and "-" indicates a transparent pixel
    """
    def __init__(self, filename=None):
        self.filename = filename
        bitmap = []
        bitmapWidth = 0  # keep track of width
        if filename is not None:
		    f = open(filename, 'r')
		    for line in f:
		        if not re.match(r'^[0-9a-fA-F\s-]+$', line):
		            raise Exception("Bitmap file contains invalid characters")
		        # Determine if widths are consistent
		        leds = line.split()
		        if bitmapWidth != 0:
		            if len(leds) != bitmapWidth:
		                raise Exception("Bitmap has different widths")
		        else:
		            bitmapWidth = len(leds)
		        bitmap.append(leds)
		    f.close()
	    self.bitmap = bitmap
            
            
            
