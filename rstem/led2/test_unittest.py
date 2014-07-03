#!/usr/bin/python3

import unittest
import os
from rstem import led2

# TODO: single setup for all testcases????
# TODO: make hardware versions that you can optionally skip

if __name__ == '__main__':
    unittest.main()
    
def query(question):
    ret = int(input(question + "  [yes=1,no=0]: "))
    if ret == 1:
        return True
    elif ret == 0:
        return False
    else:
        raise ValueError("Please only provide 1 or 0. Thank You!")

class PrivateFunctions(unittest.TestCase):
    
    def test_valid_color(self):
        for i in range(16):
            self.assertTrue(led2._valid_color(i))
            self.assertTrue(led2._valid_color(hex(i)[2:]))
        self.assertTrue(led2._valid_color('-'))
        self.assertFalse(led2._valid_color(17))
        self.assertFalse(led2._valid_color(-1))
        # random invalid characters
        self.assertFalse(led2._valid_color('j'))
        self.assertFalse(led2._valid_color('%'))
        self.assertFalse(led2._valid_color('10'))  #TODO : should we allow none hex versions?
        
    def test_convert_color(self):
        self.assertRaises(ValueError, led2._convert_color('J')) # FIXME: syntax correct?
        for i in range(16):
            self.assertEquals(led2._convert_color(hex(i)[2:]), i)
            self.assertEquals(led2._convert_color(i), i)

class PrimativeFunctions(unittest.TestCase):
    
    def setUp(self):
        led2.initGrid(1,2)
        
    def tearDown(self):
        led2.close()
        
    def test_point(self):
        for y in range(8):
            for x in range(16):
                # test without a color
                self.assertEquals(led2.point(x,y), 1)
                self.assertEquals(led2.point((x,y)), 1)
                # test with all the colors
                for color in range(17):
                    self.assertEquals(led2.point(x,y), 1)
                    self.assertEquals(led2.point((x,y)), 1)
        self.assertEquals(led2.show(), 1)
        self.assertTrue(query("Is the entire matrix at full brightness?"))
        
    def test_line(self):
        self.assertEquals(led2.point((0,0),(15,7)), 1)
        self.assertEquals(led2.show(), 1)
        self.assertTrue(query("Is there a line from (0,0) to (15,7)?"))
        
class TestingSprites(unittest.TestCase):
    
    def setUp(self):
        led2.initGrid(1,2)
        
    def tearDown(self):
        led2.close()
        
    def test_init_sprite(self):
        if font_path is None: # if none, set up default font location
            this_dir, this_filename = os.path.split(__file__)
        self.assertEquals(led2.sprite(this_dir + "/test_sprite"), 1)
        self.assertEquals(led2.show(), 1)
        self.assertTrue(query("Do you see the test pattern on the left led matrix?"))
        self.assertEquals(led2.fill(0), 1)
        self.assertEquals(led2.show(), 1)
        self.assertFalse(query("What about now?"))
        
    def test_text(self):
        self.assertNotEquals(led2.text("jon"), 0)
        self.assertEquals(led2.show(), 1)
        self.assertTrue(query("Is 'jon' displayed with large font?"))
        
        
