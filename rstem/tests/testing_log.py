from os.path import expanduser
import traceback
import time
import os
import csv
import testing

class TestLogger:
    def __init__(self):
        log_dir, symlink_name, log_file_name = self._log_name()
        print('Creating new log:', log_file_name)
        os.makedirs(log_dir, exist_ok=True)
        try: 
            os.remove(symlink_name)
        except: pass
        os.symlink(log_file_name, symlink_name)
        self.log_file = open(symlink_name, 'w')
        self.log = csv.writer(self.log_file, delimiter=',', quotechar='"')

    def _log_name(self):
        log_dir = expanduser('~/rstem_logs/')
        symlink_name = log_dir + 'testlog.txt'
        log_file_name = 'testlog.' + str(int(time.time())) + '.txt'
        return (log_dir, symlink_name, log_file_name)
        
    def write(self, func, test_type, exc):
        filename = line_num = func_name = line_text = exc_name = exc_msg = ''
        if exc:
            extracted_tb = traceback.extract_tb(exc.__traceback__)
            filename, line_num, func_name, line_text = list(extracted_tb[-1])
            exc_name = type(exc).__name__
            exc_msg = str(exc)

        self.log.writerow([
            str(func.__name__),
            str(test_type),
            exc_name,
            filename,
            line_num,
            func_name,
            exc_msg
            ])

    def close(self):
        self.log_file.close()

    def dump(self):
        log_dir, symlink_name, log_file_name = self._log_name()
        base_fmt = '{pass_fail_char:2}{test_type:5}{test_name:30}'

        # Header - 2 lines: line of labels, then line of "-" for each label.
        header_fmt = base_fmt + '{exc:40}'
        kwfmt = {
            'pass_fail_char' : '*',
            'test_name' : 'TEST NAME',
            'test_type' : 'TYPE',
            'exc' : 'EXCEPTION INFO AND END OF TRACEBACK',
            }
        print(header_fmt.format(**kwfmt))
        for key in kwfmt.keys():
            kwfmt[key] = "-" * len(kwfmt[key])
        print(header_fmt.format(**kwfmt))

        # For each line in log
        with open(symlink_name) as log:
            for row in csv.reader(log):
                test_name, test_type, exc_name, filename, line_num, func_name, exc_msg = row
                test_type_mapping = {
                    'MANUAL_OUTPUT_TEST' : 'OUT',
                    'MANUAL_INPUT_TEST' : 'IN',
                    'AUTOMATIC_TEST' : 'AUTO',
                }
                test_type = test_type_mapping[test_type]
                if exc_name:
                    pass_fail_char = 'F'
                    if exc_name == type(testing.TestSkippedException).__name__:
                        pass_fail_char = 's'
                    fmt = base_fmt + '{exc_name}:{exc_msg}'
                    if exc_msg:
                        spacer = base_fmt.format( pass_fail_char='', test_name='', test_type='')
                        fmt += '\n' + spacer + '{filename}:{line_num}:{func_name}()'
                else:
                    pass_fail_char = '-'
                    fmt = base_fmt

                print(fmt.format(
                    pass_fail_char=pass_fail_char,
                    test_name=test_name,
                    test_type=test_type,
                    exc_name=exc_name,
                    filename=filename,
                    line_num=line_num,
                    func_name=func_name,
                    exc_msg=exc_msg,
                    ))

logger = None

def create():
    global logger
    logger = TestLogger()
    
def logger_func_factory(method_name):
    def func(*args, **kwargs):
        global logger
        method = getattr(logger, method_name)
        method(*args, **kwargs)
    return func
        
for method_name in ['write', 'close', 'dump']:
    globals()[method_name] = logger_func_factory(method_name)

