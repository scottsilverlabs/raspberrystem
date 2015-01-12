from collections import defaultdict
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

    def write(self, test, test_type, exc):
        filename = line_num = func_name = line_text = exc_name = exc_msg = ''
        if exc:
            extracted_tb = traceback.extract_tb(exc.__traceback__)
            try:
                filename, line_num, func_name, line_text = list(extracted_tb[-1])
            except IndexError:
                pass
            exc_name = type(exc).__name__
            exc_msg = str(exc)

        test_func_name = str(test.__name__) if test else ""

        self.log.writerow([
            test_func_name,
            test_type,
            exc_name,
            filename,
            line_num,
            func_name,
            exc_msg
            ])

    def keyboard_interrupt(self):
        self.write(
            None,
            None,
            KeyboardInterrupt())

    def close(self):
        self.log_file.close()

    def print_summary(self):
        log_dir, symlink_name, log_file_name = self._log_name()

        # For each line in log

        with open(symlink_name) as log:
            class PassCounts:
                passed = 0
                failed = 0
                skipped = 0
                total = 0
            pass_counts_per_test_type = {}
            for t in testing.ordered_test_types:
                pass_counts_per_test_type[t] = PassCounts()
            for row in csv.reader(log):
                test_name, test_type, exc_name, filename, line_num, func_name, exc_msg = row
                if test_type:
                    if not exc_name:
                        pass_counts_per_test_type[test_type].passed += 1
                    elif exc_name == testing.TestSkippedException.__name__:
                        pass_counts_per_test_type[test_type].skipped += 1
                    else:
                        pass_counts_per_test_type[test_type].failed += 1
                    pass_counts_per_test_type[test_type].total += 1
            print("TEST SUMMARY:")
            for t in testing.ordered_test_types:
                if pass_counts_per_test_type[t].total > 0:
                    if pass_counts_per_test_type[t].passed == pass_counts_per_test_type[t].total:
                        print('\t{}: PASSED ALL TESTS ({})'.format(
                            t,
                            pass_counts_per_test_type[t].total,
                            ))
                    elif pass_counts_per_test_type[t].skipped == 0:
                        print('\t{}: passed {} of {}'.format(
                            t,
                            pass_counts_per_test_type[t].passed,
                            pass_counts_per_test_type[t].total,
                            ))
                    else:
                        print('\t{}: passed {} of {} (skipped {})'.format(
                            t,
                            pass_counts_per_test_type[t].passed,
                            pass_counts_per_test_type[t].total,
                            pass_counts_per_test_type[t].skipped,
                            ))
                expected_total = 0
                expected_total += pass_counts_per_test_type[t].passed
                expected_total += pass_counts_per_test_type[t].failed
                expected_total += pass_counts_per_test_type[t].skipped
                if expected_total != pass_counts_per_test_type[t].total:
                    print('WARNING: Counts don\'t add to total')

    def print_result_table(self):
        log_dir, symlink_name, log_file_name = self._log_name()
        base_fmt = '{pass_fail_char:2}{test_type:5}{test_name:30}'

        # Header - 2 lines: line of labels, then line of "-" for each label.
        header_fmt = base_fmt + '{exc:40}'
        kwfmt = {
            'pass_fail_char' : '*',
            'test_name' : 'TEST NAME',
            'test_type' : 'TYPE',
            'exc' : 'EXCEPTION INFO (AND END OF TRACEBACK)',
            }
        print(header_fmt.format(**kwfmt))
        for key in kwfmt.keys():
            kwfmt[key] = '-' * len(kwfmt[key])
        print(header_fmt.format(**kwfmt))

        # For each line in log
        with open(symlink_name) as log:
            for row in csv.reader(log):
                test_name, test_type, exc_name, filename, line_num, func_name, exc_msg = row
                test_type = testing.test_type_short_name(test_type)
                if exc_name:
                    pass_fail_char = 'F'
                    if exc_name == testing.TestSkippedException.__name__:
                        pass_fail_char = 's'
                    if exc_msg:
                        fmt = base_fmt + '{exc_name}:{exc_msg}'
                    else:
                        fmt = base_fmt + '{exc_name}'
                    if filename or line_num or func_name:
                        spacer = base_fmt.format( pass_fail_char='', test_name='', test_type='')
                        fmt += '\n' + spacer + '{filename}:{line_num}:{func_name}()'
                else:
                    pass_fail_char = '-'
                    fmt = base_fmt + 'PASS'

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
        print(header_fmt.format(**kwfmt))
        print('* First column is [F]ail, [s]kip, or "-" for pass')

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

method_names = [
    'write',
    'close',
    'print_summary',
    'print_result_table',
    'keyboard_interrupt'
    ]
for method_name in  method_names:
    globals()[method_name] = logger_func_factory(method_name)

