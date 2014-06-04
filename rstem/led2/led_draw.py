import os
import bitstring
from array import array
#from led_server import flush # the ttytiny controller

SIZE_OF_PIXEL = 4
SIZE_OF_MATRIX = 8*8

class LedDraw:

    def __init__(self, num_matrices, num_rows=1):
        if num_rows > num_matrices or num_matrices % 2 != 0 or num_matrices <= 0:
            raise Exception("Invalid arguments in LedDraw initialization")
            
        self.bitarray = bitstring.BitArray(length=(num_matrices*SIZE_OF_PIXEL*SIZE_OF_MATRIX))  # create a bitset of all 0's
    def _bitArrayToIntArray(self):
        # TODO: implement flipping part of bitarray for multiple rows
        return array('I', [x.uint for x in list(self.bitarray.cut(16))])
        
    def show(self):
        led_server.flush(self._bitArrayToIntArray())
        
    def erase(self, color=0x0):
        self.bitarray = bitstring.BitArray(length=(self.num_matrices*SIZE_OF_PIXEL*SIZE_OF_MATRIX))
        flush(self._bitArrayToIntArray())
        
        
    def point(self, x, y=None, color=0xF):
        # If y is not given, then x is a tuple of the point
        if y == None:
            x, y = x

        # If out of range, its off the screen - just don't display it
        if x >= 0 and y >= 0 and x < len(self.fb) and y < len(self.fb[0]):
            self.fb[x][y] = color;
