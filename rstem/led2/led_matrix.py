import os
import bitstring
import led_server     # from the attiny48 controller

SIZE_OF_PIXEL = 4     # 4 bits to represent color
DIM_OF_MATRIX = 8     # 8x8 led matrix elements

class LedMatrix:

    def __init__(self, num_rows=1, num_cols=1, zigzag=True):
        """Initializes a matrix of led matrices
        num_rows = number of led matrices set up vertically
        num_cols = number of led matrices set up horizontally
        zigzag = True if matrices set up in zigzag fashion instead of 
                    left to right on each rowm
        """
        if num_rows <= 0 or num_cols <= 0:
            raise Exception("Invalid arguments in LedDraw initialization") 
        # create a bitset of all 0's 
        self.bitarray = \
            bitstring.BitArray(length=(num_rows*num_cols*SIZE_OF_PIXEL*(DIM_OF_MATRIX**2)))
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.num_matrices = num_rows*num_cols
        
        
    def _bitArrayToByteArray(self):
        """Convert bitarray into an bytearray python type that can be given to led_server"""     
        return bytearray(self.bitarray.tobytes())
        
        
    def _pointToBitPos(self, x, y):
        """Convert the (x,y) coordinates into the bit position in bitarray
        Returns None if point not located on led matrix"""
        if y < 0 or y >= self.num_rows*DIM_OF_MATRIX \
            or x < 0 or x >= self.num_matrices/self.num_rows*DIM_OF_MATRIX:
            return None
           
        # figure out what matrix we are dealing with
        mat_col = x/DIM_OF_MATRIX
        mat_row = y/DIM_OF_MATRIX
        
        # subtract off above matrix rows so we can treat y relative to matrix row
        y = (y - mat_row*DIM_OF_MATRIX)
        
        # if on odd matrix row and zigzag enabled, we need to flip x and y coords
        if mat_row % 2 == 1 and self.zigzag:
            x = (DIM_OF_MATRIX*self.num_cols - 1) - x
            y = (DIM_OF_MATRIX - 1) - y
        
        # bit position of the first pixel (going up) of column 
        bitPosCol = (x + mat_row*DIM_OF_MATRIX*self.num_cols)*DIM_OF_MATRIX*SIZE_OF_PIXEL  
        bitPosColOffset = (DIM_OF_MATRIX - 1 - y)*SIZE_OF_PIXEL # flip y to move up
        
        bitPos = bitPosCol + bitPosColOffset  
        
        # swap nibble (low to high, high to low) for the led_server
        if bitPos % 8 = 0: # beginning of byte
            bitPos += 4
        elif bitPos % 8 = 4: # middle of byte
            bitPos -= 4
        else:
            assert False, "bitPos is not nibble aligned"
            
        return bitPos
        
        
    def show(self):
        led_server.flush(self._bitArrayToByteArray())  # give frame buffer to led_server
        if __debug__:
            for y in range(self.num_rows*DIM_OF_MATRIX):
                for x in range(self.num_cols*DIM_OF_MATRIX):
                    bitPos = self._pointToBitPos(x,y)
                    print (self.bitarray[bitPos : bitPos+SIZE_OF_PIXEL].hex),
                print " " #print newline
        
    def erase(self, color=0x0):
        self.bitarray = \
            bitstring.BitArray(length=(self.num_matrices*SIZE_OF_PIXEL*DIM_OF_MATRIX**2))
        self.show()
        
        
    def point(self, x, y, color=0xF):
        """Adds point to bitArray"""
        if color < 0x0 or color > 0xF:
            print "Invalid Color"
            return
        bitPos = self._pointToBitPos(x, y)
        if bitPos != None:
            self.bitarray[bitPos:bitPos+4] = color  # set 4 bits
            
            
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
            
            
            
