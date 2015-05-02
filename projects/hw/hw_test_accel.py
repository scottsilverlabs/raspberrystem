from rstem.accel import Accel
import traceback
import sys
import time
import os


def failed(s, tb=False):
    if tb:
        print(traceback.format_exc())
    print("ERROR: ", s)
    print("TEST FAILED")
    sys.exit()

try:
    a = Accel()
except:
    failed("Accel() could not be intialized", True)

print("INFO: Accel found.")

def near(actual, expected):
    is_near = True
    for a, e in zip(actual, expected):
        if abs(a-e) > 0.07:
            is_near = False
    return is_near


def verify(expected_forces):
    try:
        print("STABILIZING", end="")
        sys.stdout.flush()
        for i in range(200):
            if near(a.forces(), expected_forces):
                break
            print(".", end="")
            sys.stdout.flush()
            time.sleep(0.1)
        else:
            return False
        print()
        print("LOCKING", end="")
        sys.stdout.flush()
        lock = 0
        for i in range(200):
            if near(a.forces(), expected_forces):
                print("*", end="")
                lock += 1
            else:
                print(".", end="")
                lock = 0
            if lock > 20:
                break
            sys.stdout.flush()
            time.sleep(0.1)
        else:
            return False
        return True
    finally:
        print()

"""
while True:
    print("{: 03.3f} {: 03.3f} {: 03.3f}".format(*a.forces()))
    time.sleep(0.1)
"""

print("Tilt the RStem left, by putting a Lid Spacer under the right side.")
if not verify((0.540, 0, 0.814)):
    failed("Left tilt failed")

print("Sit the RStem flat on the table, with Z pointing up.")
if not verify((0, 0, 1)):
    failed("Sit flat failed")

print("Sit the RStem vertically on the table, with Y pointing up.")
if not verify((0, 1, 0)):
    failed("Sit vertical failed")

