import os
import bitstring
from array import array
import led_server     # from the attiny48 controller

SIZE_OF_PIXEL = 4     # 4 bits to represent color
DIM_OF_MATRIX = 8     # 8x8 led matrix elements

class LedDraw:

    def __init__(self, num_matrices, num_rows=1):
        if num_rows > num_matrices or num_matrices % 2 != 0 or num_matrices <= 0:
            raise Exception("Invalid arguments in LedDraw initialization")  
        self.bitarray = bitstring.BitArray(length=(num_matrices*SIZE_OF_PIXEL*(DIM_OF_MATRIX**2)))  # create a bitset of all 0's
        self.num_rows = num_rows
        self.num_cols = num_matrices/num_rows
        self.num_matrices = num_matrices
        
    def _bitArrayToByteArray(self):
        """Convert bitarray into an int array that can be given to led_server"""
        # TODO: implement flipping part of bitarray for multiple rows
        return bytearray([x.uint for x in list(self.bitarray.cut(8))])
#        return array('I', [x.uint for x in list(self.bitarray.cut(16))])
        
    def _pointToBitPos(self, x, y):
        """Convert the (x,y) coordinates into the bit position in bitarray
        Returns None if point not located on led matrix"""
        # TODO: implement support for multiple matrix rows
        if y < 0 or y >= self.num_rows*DIM_OF_MATRIX \
            or x < 0 or x >= self.num_matrices/self.num_rows*DIM_OF_MATRIX:
            return None
            
#        mat_col = floor(
            
        # bottom left corner of first matrix is bitpos = 0, 
        # - bit pos incrememnt going up matrix column were bitpos 7*4 is top left of first matrix
        # - then repeats so bitpos 8*4 is pixel to right of bottom left of first matrix
        bitPosColumn = x*DIM_OF_MATRIX*SIZE_OF_PIXEL  # bit position of the first pixel (going up) of column 
        bitPosRow = (DIM_OF_MATRIX-1 - y)*SIZE_OF_PIXEL  # flip y coordinate around
        
        #TODO: implement bitPosMatrix variable
        
        return bitPosColumn + bitPosRow
        
    def show(self):
        led_server.flush(self._bitArrayToByteArray())  # give frame buffer to led_server
        
        # debugging
        for y in range(self.num_rows*DIM_OF_MATRIX):
            for x in range(self.num_cols*DIM_OF_MATRIX):
                bitPos = self._pointToBitPos(x,y)
                print (self.bitarray[bitPos : bitPos+4].hex),
            print " "
        
    def erase(self, color=0x0):
        self.bitarray = bitstring.BitArray(length=(self.num_matrices*SIZE_OF_PIXEL*SIZE_OF_MATRIX))
        self.show()
        
        
    def point(self, x, y, color=0xF):
        """Adds point to bitArray"""
        if color < 0x0 or color > 0xF:
            print "Invalid Color"
            return
        
        bitPos = self._pointToBitPos(x, y)
        if bitPos != None:
            self.bitArray[bitPos:bitPos+4] = color  # set 4 bits
            
    def _sign(self, n):
        return 1 if n >= 0 else -1
            
    def line(self, point_a, point_b, color=0xF):
        """Create a line from point_a to point_b"""       
        if color < 0x0 or color > 0xF:
            print "Invalid Color"
            return
    
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
            
            
            
