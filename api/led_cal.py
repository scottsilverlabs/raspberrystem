import os

class led_cal:
    LED_CAL_FILE=os.path.expanduser("~/.ledcal")
    
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
                n = int(_input_string("Enter the " + name_of_num, default))
            except (ValueError, TypeError):
                print "Error: Invalid number"
                continue

            if not (min_num <= n <= max_num):
                print "Error: The %s must be %d through %d" % (name_of_num, min_num, max_num)
                continue

            break

        return n
        
    def _input_row_or_col(self, matrix, is_row, default_vals):
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
            matrices += [[list(s) for s in line.split(",")]]

        return matrices

    def _save_calibration(self, matrices):
        f = open(LED_CAL_FILE, "w")
        for i in matrices:
            colstr = "".join([str(n) for n in matrices[0][0]])
            rowstr = "".join([str(n) for n in matrices[0][1]])
            f.write("%s,%s\n" % (colstr, rowstr))
        f.close()
        _restore_calibration(server)

        return matrices

    def recalibrate(self):
        print "recalibrate"
        previous_matrices = _restore_calibration(server, force_default_order=True)
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
