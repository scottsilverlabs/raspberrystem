import testing_log
import importlib
from functools import wraps
import os
import sys

SEPARATOR= '\n' + '=' * 78

class TestFailureException(Exception):
    pass

class TestSkippedException(TestFailureException):
    pass

def map_exception(choice):
    exception_mapping = {
        'p' : 0,
        'f' : TestFailureException('MANUAL_FAIL'),
        's' : TestSkippedException('MANUAL_SKIP'),
        't' : TestFailureException('TIMEOUT'),
    }
    return choice if isinstance(choice, Exception) else exception_mapping[choice]

def enum(*names):
    for i, name in enumerate(names):
        globals()[name] = i
    return names

ordered_test_types = enum(
    'MANUAL_OUTPUT_TEST',
    'MANUAL_INPUT_TEST',
    'AUTOMATIC_TEST',
    'KEYBOARD_INTR',
    )

def test_type_short_name(test_type):
    test_type_mapping = {
        'AUTOMATIC_TEST' : 'AUTO',
        'MANUAL_OUTPUT_TEST' : 'OUT',
        'MANUAL_INPUT_TEST' : 'IN',
    }
    try:
        return test_type_mapping[test_type]
    except KeyError:
        return "ERR"

def automatic(func):
    @wraps(func)
    def wrapper():
        print(SEPARATOR)
        print('AUTOMATIC TEST: {0}'.format(func.__name__))
        try:
            passed = func()
            if passed:
                print('--> PASSED')
                exc = 0
            else:
                print('--> FAILED')
                exc = TestFailureException('AUTOMATIC_TEST_FAIL')
        except Exception as e:
            print('--> FAILED BY EXCEPTION:' + str(e))
            exc = e
        testing_log.write(func, ordered_test_types[wrapper.test_type], exc)
    wrapper.test_type = AUTOMATIC_TEST
    return wrapper

def manual_output(func):
    @wraps(func)
    def wrapper():
        choice = 'r'
        print(SEPARATOR)
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
                print('--> FAILED BY EXCEPTION:' + str(e))
                break
            while True:
                ret = input('Check the output - pass, fail, retry or skip? [P/f/r/s]: ').strip()
                if not ret:
                    ret = 'p'
                choice = ret[0].lower()
                if choice in 'pfrs':
                    break
                print('INVALID CHOICE!')
        testing_log.write(func, ordered_test_types[wrapper.test_type], map_exception(choice))
    wrapper.test_type = MANUAL_OUTPUT_TEST
    return wrapper

def manual_input(func):
    @wraps(func)
    def wrapper():
        print(SEPARATOR)
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
        testing_log.write(func, result)
    wrapper.test_type = MANUAL_INPUT_TEST
    return wrapper

if __name__ == '__main__':
    module_name = 'test_' + sys.argv[1]
    module = importlib.import_module(module_name)
    funcs = [getattr(module, func) for func in dir(module)]
    tests = [func for func in funcs if hasattr(func, 'test_type')]
    test_types = set([test.test_type for test in tests])

    # For each test type, in the defined order, run the tests
    testing_log.create()
    try:
        for t, name in enumerate(ordered_test_types):
            if t in test_types:
                # Run all tests of the given type
                for test in tests:
                    if test.test_type == t:
                        test()
    except KeyboardInterrupt as e:
        testing_log.keyboard_interrupt()
    testing_log.close()

    print(SEPARATOR)
    testing_log.print_result_table()

    print(SEPARATOR)
    testing_log.print_summary()

