#!/usr/bin/env python3
#
# Copyright (c) 2014, Scott Silver Labs, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys
from setuptools import setup, find_packages, Extension
from distutils.command.install import install as _install

# check python version is good
if sys.version_info[0] == 2:
    if not sys.version_info >= (2, 6):
        raise ValueError('This package requires Python 2.6 or above')
elif sys.version_info[0] == 3:
    if not sys.version_info >= (3, 2):
        raise ValueError('This package requires Python 3.2 or above')
else:
    raise ValueError('What version of Python is this?!')

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def _post_install(dir):
    from subprocess import call
    if os.system("grep 'BCM2708' /proc/cpuinfo > /dev/null") == 0:
        call("./pkg/postinstall")
    else:
        print("WARNING: GPIO, I2C, and SPI are unsupported on this non-RaspberryPi!")

# Post installation task to setup raspberry pi
class install(_install):
    def run(self):
        _install.run(self)
        self.execute(_post_install, (self.install_lib,), msg="Running post install task...")

# C extension wrappers
led_driver =  Extension('rstem.led_matrix.led_driver', sources = ['rstem/led_matrix/led_driver.c'])
accel = Extension('rstem.accel', sources = ['rstem/accel.c'])

# Attempt to add numpy, if not install require it in the setup_requires.
build_requires = []
try:
    import numpy
except:
    build_requires = ['numpy>=1.5.1']

setup(
    name = "raspberrystem",
    version = "0.0.2",
    author = "Brian Silverman",
    author_email = "bri@raspberrystem.com",
    description = ("RaspberrySTEM Educational and Hobbyist Development Kit "
                    "based on the Raspberry Pi."),
    license = "BSD",
    keywords = ["raspberrypi", "stem"],
    url = "https://raspberrystem.com",
    packages = find_packages(),
    include_package_data = True,
    long_description = read('README.md'),
    # use https://pypi.python.org/pypi?%3Aaction=list_classifiers as help when editing this
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Education",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
    ],
    install_requires=['numpy', 'pygame'],  # insert python packages as needed
    cmdclass={'install': install},  # overload install command
    include_dirs = [numpy.get_include()],  # Get numpy/arrayobject.h
    setup_requires = build_requires,
    test_suite = 'tests',
    ext_modules = [led_driver, accel]  # c extensions defined above
)
