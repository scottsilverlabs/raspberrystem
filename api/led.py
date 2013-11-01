import time
import os
import sys
import fcntl
from subprocess import *

LED_CAL_FILE=os.path.expanduser("~/.ledcal")

def _input_string(prompt="", default=None):
    if default:
        prompt += " [%s]" % default
    prompt += ": "
    s = raw_input(prompt).strip()
    return s if len(s) else default

def _input_num(name_of_num, min_num, max_num, default=None):
    while True:
        try:
            n = int(_input_string("Enter the " + name_of_num, default))
        except (ValueError, TypeError):
            print "Error: Invalid number"
            continue

        if not (min_num <= n <= max_num):
            print "Error: The %s must be %d through %d" % (name_of_num, min_num, max_num)
            continue

        break

    return n
    
def _input_row_or_col(matrix, is_row, default_vals):
    s = "row" if is_row else "column"
    while True:
        vals = []
        for val in range(8):
            erase()
            if is_row:
                line((0, val), (get_fb_width(), val))
            else:
                line((val, 0), (val, get_fb_height()))
            show()

            default = default_vals[val] if default_vals else None
            name_of_num = "%s currently displayed on LED matrix %d" % (s, matrix)
            vals += [_input_num(name_of_num, 1, 8, default)]

        if len(set(vals)) != len(vals):
            print "Hmmmm, weird.  All %ss entered should be unique, but they aren't" % s
            print "The values entered were: " + str(vals)
            print "Try again..."
            continue
        break

    remapped_vals = range(8)
    for i, val in enumerate(vals):
        remapped_vals[val - 1] = i + 1
    return remapped_vals

def _send_cmd(cmd, data):
    pipe.write(cmd + ("%02X" % len(data)) + data)

def _restore_calibration(force_default_order=False):
    ORDERED_MATRIX_LINES = ["01234567,01234567"]
    if force_default_order:
        lines = ORDERED_MATRIX_LINES
    else:
        # Read in all nonempty lines of cal file
        try:
            lines = [line.strip() for line in open(LED_CAL_FILE).readlines() if len(line.strip())]
        except IOError:
            lines = ORDERED_MATRIX_LINES

    for line, mapping in enumerate(lines):
        _send_cmd("o", "%d%s" % (line, mapping))

    matrices = []
    for line in lines:
        matrices += [[list(s) for s in line.split(",")]]

    return matrices

def _save_calibration(matrices):
    f = open(LED_CAL_FILE, "w")
    for i in matrices:
        colstr = "".join([str(n) for n in matrices[0][0]])
        rowstr = "".join([str(n) for n in matrices[0][1]])
        f.write("%s,%s\n" % (colstr, rowstr))
    f.close()
    _restore_calibration()

    return matrices

def _init_module():
    erase()
    global pipe
    pipe = Popen("api/led_server", shell=True, stdin=PIPE).stdin
    _restore_calibration()

def _main():
    while 1:
        for i in range(8):
            for j in range(8):
                led.point(x, y)
                led.show()
                time.sleep(0.5);
                led.point(x, y, color=0)

def bound(x, y=None, color=1):
    # If y is not given, then x is a tuple of the point
    if y == None:
        x, y = x

    if x >= 8:
        x = 7
    elif x < 0:
        x = 0

    if y >= 8:
        y = 7
    elif y < 0:
        y = 0

    return (x, y)

def sign(n):
    return 1 if n >= 0 else -1

def erase(color=0):
    global fb
    fb = [[color]*8 for i in range(8)]

def point(x, y=None, color=1):
    # If y is not given, then x is a tuple of the point
    if y == None:
        x, y = x

    # If out of range, its off the screen - just don't display it
    try:
        fb[int(x)][int(y)] = color;
    except IndexError:
        pass

def line(point_a, point_b, color=1):
    point_a = (int(point_a[0]), int(point_a[1]))
    point_b = (int(point_b[0]), int(point_b[1]))
    x_diff = point_a[0] - point_b[0]
    y_diff = point_a[1] - point_b[1]
    step = sign(x_diff) * sign(y_diff)
    width = abs(x_diff) + 1
    height = abs(y_diff) + 1
    if (width > height):
        start_point = point_a if x_diff < 0 else point_b
        for x_offset in range(int(width)):
            point(
                start_point[0] + x_offset,
                start_point[1] + step*(x_offset*height/width),
                color=color)
    else:
        start_point = point_a if y_diff < 0 else point_b
        for y_offset in range(int(height)):
            point(
                start_point[0] + step*(y_offset*width/height),
                start_point[1] + y_offset,
                color=color)
    
def rect(start, dimensions, color=1):
    x, y = start
    width, height = dimensions
    line((x, y), (x, y + height), color=color)
    line((x, y + height), (x + width, y + height), color=color)
    line((x + width, y + height), (x + width, y), color=color)
    line((x + width, y), (x, y), color=color)

def show():
    s = "0"
    for x in range(8):
        col = 0
        for y in range(8):
            col |= fb[x][y] << (8-y-1)
        s += "%02X" % col
    _send_cmd("m", s);

def recalibrate():
    print "recalibrate"
    previous_matrices = _restore_calibration(force_default_order=True)
    print previous_matrices
    num_matrices = _input_num("number of LED matrices", 1, 8, len(previous_matrices))

    matrices = []
    for i in range(num_matrices):
        default_cols = previous_matrices[i][0] if i < len(previous_matrices) else None
        default_rows = previous_matrices[i][1] if i < len(previous_matrices) else None
        print default_cols, default_rows
        cols = _input_row_or_col(i, False, default_cols)
        rows = _input_row_or_col(i, True, default_rows)
        matrices += [(cols, rows)]
    print matrices

    _save_calibration(matrices)
    
_init_module()
if __name__ == "__main__":
    _main()

