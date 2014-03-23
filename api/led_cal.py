import os
from collections import namedtuple

MatrixMapping = namedtuple('MatrixMapping', 'colmap rowmap')
    
class LedCal:
    LED_CAL_FILE=os.path.expanduser("~/.ledcal")
    MATRIX_COLS=8
    MATRIX_ROWS=8
    
    def __init__(self, server):
        self.server = server
        self._restore_calibration(server)

    def _input_string(self, prompt="", default=None):
        if default:
            prompt += " [%s]" % default
        prompt += ": "
        s = raw_input(prompt).strip()
        return s if len(s) else default

    def _input_num(self, name_of_num, min_num, max_num, default=None):
        while True:
            try:
                n = int(self._input_string("Enter the " + name_of_num, default))
            except (ValueError, TypeError):
                print "Error: Invalid number"
                continue

            if not (min_num <= n <= max_num):
                print "Error: The %s must be %d through %d" % (name_of_num, min_num, max_num)
                continue

            break

        return n
        
    def h(self, x):
        self.server.send_cmd("h", "0" + str(x))

    def v(self, x):
        self.server.send_cmd("v", "0" + str(x))

    def _input_row_or_col(self, matrix, is_row, default_vals):
        s = "row" if is_row else "column"
        first = "bottommost" if is_row else "leftmost"
        last = "topmost" if is_row else "rightmost"
        while True:
            vals = []
            for val in range(8):
                self.server.send_cmd("h" if is_row else "v", str(matrix) + str(val))

                default = str(default_vals.index(str(val))) if default_vals else None
                fmt = "%s currently displayed on LED matrix %d (%s is 0, %s is 7)" 
                name_of_num = fmt % (s, matrix, first, last)

                vals += [self._input_num(name_of_num, 0, 7, default)]

            if len(set(vals)) != len(vals):
                print "Hmmmm, weird.  All %ss entered should be unique, but they aren't" % s
                print "The values entered were: " + str(vals)
                print "Try again..."
                continue
            break

        remapped_vals = range(8)
        for i, val in enumerate(vals):
            remapped_vals[val] = i
        return remapped_vals

    def _restore_calibration(self, server, force_default_order=False):
        ORDERED_MATRIX_LINES = ["01234567,01234567"]
        if force_default_order:
            lines = ORDERED_MATRIX_LINES
        else:
            # Read in all nonempty lines of cal file
            try:
                lines = [
                    line.strip() for line in open(self.LED_CAL_FILE).readlines() 
                        if len(line.strip())
                    ]
            except IOError:
                lines = ORDERED_MATRIX_LINES

        for line, mapping in enumerate(lines):
            server.send_cmd("o", "%d%s" % (line, mapping))

        matrices = []
        for line in lines:
            colmap, rowmap = (list(s) for s in line.split(","))
            matrices += [MatrixMapping(colmap, rowmap)]
        
        if not force_default_order:
            self.matrices = matrices

        return self.matrices

    def _save_calibration(self, matrices):
        f = open(self.LED_CAL_FILE, "w")
        for m in matrices:
            colstr = "".join([str(n) for n in m.colmap])
            rowstr = "".join([str(n) for n in m.rowmap])
            f.write("%s,%s\n" % (colstr, rowstr))
        f.close()
        self._restore_calibration(self.server)

        return matrices

    def get_matrix_origin(self, m):
        # For now, assume matrices are horizontally laid out, in order.
        return (m * self.MATRIX_COLS, 0)

    def get_num_matrices(self):
        return len(self.matrices)

    def get_fb_width(self):
        return self.get_num_matrices() * self.get_matrix_width()

    def get_fb_height(self):
        return self.get_matrix_height()

    def get_matrix_width(self):
        return self.MATRIX_COLS

    def get_matrix_height(self):
        return self.MATRIX_ROWS

    def recalibrate(self):
        print "Recalibrating..."
        previous_matrices = self._restore_calibration(self.server, force_default_order=True)
        num_matrices = self._input_num("number of LED matrices", 1, 8, len(previous_matrices))

        matrices = []
        for i in range(num_matrices):
            default_cols = previous_matrices[i].colmap if i < len(previous_matrices) else None
            default_rows = previous_matrices[i].rowmap if i < len(previous_matrices) else None
            cols = self._input_row_or_col(i, False, default_cols)
            rows = self._input_row_or_col(i, True, default_rows)
            matrices += [MatrixMapping(cols, rows)]

        self._save_calibration(matrices)
