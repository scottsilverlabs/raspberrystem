#!/usr/bin/env python


import subprocess

# open up the accel test program in a new window 
proc = subprocess.Popen(['lxterminal', '-e', './accel_test_aux.py'])

proc.wait()