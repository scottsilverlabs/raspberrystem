import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "RaspberrySTEM",
    version = "0.0.1",
    author = "Brian Silverman",
    author_email = "bri@raspberrystem.com",
    description = ("RaspberrySTEM Educational and Hobbyist Development Kit "
                    "based on the Raspberry Pi."),
    license = "BSD",
    keywords = "raspberry pi",
    url = "https://github.com/scottsilverlabs/raspberrystem",
    packages=['accel', 'gpio', 'led'],
    long_description=read('README.md'),
    # use https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Education",
        "License :: OSI Approved :: Apache Software License",
    ],
    install_requires=[
        'bitstring',
    ],
)

# TODO: register python package to https://pypi.python.org/pypi
