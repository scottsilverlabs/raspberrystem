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
"""
This module provides interfaces to the buttons and switches in the Button RaspberrySTEM Cell.
"""

import os
from struct import pack
from fcntl import ioctl

#
# MMA8653 Register Map
#
STATUS =        0x00
OUT_X_MSB =     0x01
OUT_X_LSB =     0x02
OUT_Y_MSB =     0x03
OUT_Y_LSB =     0x04
OUT_Z_MSB =     0x05
OUT_Z_LSB =     0x06
SYSMOD =        0x0B
INT_SOURCE =    0x0C
WHO_AM_I =      0x0D
XYZ_DATA_CFG =  0x0E
PL_STATUS =     0x10
PL_CFG =        0x11
PL_COUNT =      0x12
PL_BF_ZCOMP =   0x13
PL_THS_REG =    0x14
FF_MT_CFG =     0x15
FF_MT_SRC =     0x16
FF_MT_THS =     0x17
FF_MT_COUNT =   0x18
ASLP_Count =    0x29
CTRL_REG1 =     0x2A
CTRL_REG2 =     0x2B
CTRL_REG3 =     0x2C
CTRL_REG4 =     0x2D
CTRL_REG5 =     0x2E
OFF_X =         0x2F
OFF_Y =         0x30
OFF_Z =         0x31

MMA8653_DEVICE_ADDR = 0x1D

#
# I2C_SLAVE from header <linux/i2c-dev.h>
#
I2C_SLAVE = 0x0703


class Accel(object):
    def __init__(self, bus=1):
        self.fd = os.open("/dev/i2c-{}".format(bus), os.O_RDWR)
        ioctl(self.fd, I2C_SLAVE, MMA8653_DEVICE_ADDR)
        os.write(self.fd, pack('bb', CTRL_REG1, 0x00))
        os.write(self.fd, pack('bb', XYZ_DATA_CFG, 0x01))
        os.write(self.fd, pack('bb', CTRL_REG2, (1 << 4) | (1 << 3) | (1 << 1) | 1))
        os.write(self.fd, pack('bb', CTRL_REG1, 0x01))

    def angles(self):
        os.write(self.fd, pack('b', 0x00))
        x = os.read(self.fd, 7)
        print(x)
        x, y, z = (1, 2, 3)
        return (x, y, z)

    def __del__(self):
        os.close(self.fd)

__all__ = ['Accel']
