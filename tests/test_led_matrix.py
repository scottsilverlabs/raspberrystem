#!/usr/bin/python3

import pytest
import os
from rstem import led_matrix

# TODO: single setup for all testcases????
# TODO: make hardware versions that you can optionally skip

def query(question):
    ret = int(input(question + "  [yes=1,no=0]: "))
    if ret == 1:
        return True
    elif ret == 0:
        return False
    else:
        raise ValueError("Please only provide 1 or 0. Thank You!")
        

def test_valid_color():
    for i in range(16):
        assert led_matrix._valid_color(i)
        assert led_matrix._valid_color(hex(i)[2:])
    assert led_matrix._valid_color('-')
    assert led_matrix._valid_color(17)
    assert led_matrix._valid_color(-1) == 0
    # random invalid characters
    assert led_matrix._valid_color('j') == 0
    assert led_matrix._valid_color('%') == 0
    assert led_matrix._valid_color('10') == 0
        
def test_convert_color():
    with pytest.raises(ValueError):
        led_matrix.convert_color('J')
    for i in range(16):
        assert led_matrix._convert_color(hex(i)[2:]) == i
        assert led_matrix._convert_color(i) == i
        
def test_init_grid():
    led_matrix.cleanup()
    for math_coords in [True, False]:
        for angle in [0, 90, 180, 270]:
            led_matrix.cleanup()
            led_matrix.init_grid(angle=angle, math_coords=math_coords)
            for y in range(0, led_matrix.height(), 8):
                for x in range(0, led_matrix.width(), 8):
                    led_matrix.text(str(x + x*y), (x,y))
            led_matrix.show()
            if math_coords:
                assert query("Do you see numbers (rotated correctly) going from left to right and bottom to top?")
            else:
                assert query("Do you see numbers (rotated correctly) going from left to right and top to bottom?")
                
            try:
                input("Please rotate the screen 90 degres then press ENTER.")
            except SyntaxError:
                pass
    

        
def test_line(self):
    led_matrix.init_grid()
    led_matrix.line((0,0), (led_matrix.width()-1, led_matrix.height()-1))
    led_matrix.show()
    assert query("Is there a line from (0,0) to (%s,%s)?" % led_matrix.widht()-1, led_matrix.height()-1)
        
        
        
