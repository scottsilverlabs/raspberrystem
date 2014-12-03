import testing_log
import importlib
from functools import wraps
import os
import sys

def enum(*names):
    for i, name in enumerate(names):
        globals()[name] = i
    return names

enum(
    'RESULT_PASSED',
    'RESULT_FAILED',
    'RESULT_SKIPPED',
    'RESULT_TIMEOUT',
    )

ordered_test_types = enum(
    'MANUAL_OUTPUT',
    'MANUAL_INPUT',
    )

def manual_output(func):
    @wraps(func)
    def wrapper():
        choice = 'r'
        print("=" * 72)
        while choice == 'r':
            print('MANUAL OUTPUT TEST: {0}'.format(func.__name__))
            print('VERIFY THE FOLLOWING:')
            for line in func.__doc__.split('\n'):
                print('\t' + line)
            input('Press Enter to start test:')
            try:
                func()
            except Exception as e:
                choice = e
                print('TEST FAILED BY EXCEPTION:')
                print(e)
                break
            while True:
                ret = input('Check the output - pass, fail, retry or skip? [P/f/r/s]: ').strip()
                if not ret:
                    ret = 'p'
                choice = ret[0].lower()
                if choice in 'pfrs':
                    break
                print("INVALID CHOICE!")
        testing_log.write(func, choice)
    wrapper.test_type = MANUAL_OUTPUT
    return wrapper

def manual_input(func):
    @wraps(func)
    def wrapper():
        print("=" * 72)
        print('MANUAL INPUT TEST: {0}'.format(func.__name__))
        print('PROVIDE THE FOLLOWING INPUT:')
        for line in func.__doc__.split('\n'):
            print('\t' + line)
        input('Press Enter to start test:')
        # Requires timeout
        try:
            result = func()
        except e:
            result = e
        testing_log.write(func, choice)
    wrapper.test_type = MANUAL_INPUT
    return wrapper

if __name__ == '__main__':
    module_name = 'test_' + sys.argv[1]
    module = importlib.import_module(module_name)
    funcs = [getattr(module, func) for func in dir(module)]
    tests = [func for func in funcs if hasattr(func, 'test_type')]
    test_types = set([test.test_type for test in tests])

    # For each test type, in the defined order
    testing_log.new()
    for t, name in enumerate(ordered_test_types):
        if t in test_types:
            # Run all tests of the given type
            for test in tests:
                if test.test_type == t:
                    test()
    testing_log.close()

    print("=" * 72)
    print("SUMMARY:")
    testing_log.dump()

