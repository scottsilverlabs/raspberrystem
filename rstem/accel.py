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
'''
This module provides interfaces to the Accelerometer RaspberrySTEM Cell.  An
Accelerometer allows a program to detemine which way the RaspberrySTEM is
oriented and/or moving.
'''

import os
import time
from struct import pack, unpack
from fcntl import ioctl
from ctypes import create_string_buffer, sizeof, string_at
from ctypes import c_int, c_uint16, c_ushort, c_short, c_char, POINTER, Structure

#
# Required defs from <linux/i2c.h>
#
class i2c_msg(Structure):
    _fields_ = [
        ('addr', c_uint16),
        ('flags', c_ushort),
        ('len', c_short),
        ('buf', POINTER(c_char))
        ]

class i2c_rdwr_ioctl_data(Structure):
    _fields_ = [
        ('msgs', POINTER(i2c_msg)),
        ('nmsgs', c_int)
        ]

I2C_SLAVE   = 0x0703
I2C_RDWR    = 0x0707
I2C_M_RD    = 0x0001

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
I2C_BUS = 1

# Allowed full scale settings: 2, 4, 8 (in 'g')
FULL_SCALE = 4

class Accel(object):
    def __init__(self):
        # i2c_bcm2708 driver only support repeated-start transactions (which
        # the MMA8653 requires) if the 'combined' parameter is set.
        with  open('/sys/module/i2c_bcm2708/parameters/combined', 'w') as f:
            f.write('1\n')

        # Open I2C bus device, and set Accelerometer device address.
        self.fd = os.open('/dev/i2c-{}'.format(I2C_BUS), os.O_RDWR)
        ioctl(self.fd, I2C_SLAVE, MMA8653_DEVICE_ADDR)

        # Configure all device registers while in standby mode (see app note AN4083)
        os.write(self.fd, pack('bb', CTRL_REG1, 0x00))

        full_scale_setting = { 2 : 0x00, 4 : 0x01, 8 : 0x02 }[FULL_SCALE]
        os.write(self.fd, pack('bb', XYZ_DATA_CFG, full_scale_setting))
        self.resolution = { 2 : 256, 4 : 128, 8 : 64 }[FULL_SCALE]

        # All other regs use defaults.  Sleep mode is a don't care, as max
        # power consumption is minimal (< 1mw).

        # Set ACTIVE.  All other bits default (Data rate 800Hz, normal mode)
        os.write(self.fd, pack('bb', CTRL_REG1, 0x01))

        # Verify device is who we think it is
        # NOTE: Must retry, as self._read() is not guaranteed.
        TRIES = 10
        for i in range(TRIES):
            id = self._read(WHO_AM_I)[0]
            if id == 0x5A:
                break
            time.sleep(0.001)
        if i + 1 == TRIES:
            raise IOError('MMA8653 Accelerometer is not returning correct ID ({})'.format(id))

    def _read(self, register, bytes_to_read=1):
        '''Read bytes from Accelerometer, starting at `register`.

        Reads from an arbitrary register require writing the register number, a
        repeated-start, and the reading the register value.

        Unfortunately, the MMA8653 appears to be a bit flaky, and although a
        repeated-start transaction works most of the time, it sometimes gets
        the MMA8653 in a funky state (specifically, it sometimes returns
        nonsense values, even though it always correctly responds with ACKs on
        the bus).

        As a workaround, we do two things:
            - If the register is low, we do not use a repeated-start
              transaction, and instead use os.read() to read from regsiter 0 up
              through the requested registers using the parts auto-increment
              feature.  This works always, but only works for low registers
              (STATUS and OUT_?_?SB)
            - We add a read of one byte after the repeated-start transaction.
              This appears to leave the device in a state where it is
              responding correctly MOST of the time, in testing.  But beware -
              this means you can't trust reads from high registers, and may
              need to retry them.
        '''
        if bytes_to_read > 8:
            raise ValueError('MMA8653 Accel. does not (seem) to allow consectutive reads > 8')

        # HW Workaround for low registers to avoid repeated-start.  See docstring.
        if register + bytes_to_read <= OUT_Z_LSB + 1:
            data = os.read(self.fd, register + bytes_to_read)
            return data[register:]

        # Create C-based I2C write message struct (1 byte register)
        buf = create_string_buffer(bytes((register,)), 1)
        write_msg = i2c_msg(
            addr=MMA8653_DEVICE_ADDR,
            flags=0,
            len=sizeof(buf),
            buf=buf
            )

        # Create C-based I2C read message struct (bytes_to_read bytes)
        buf = create_string_buffer(bytes_to_read)
        read_msg = i2c_msg(
            addr=MMA8653_DEVICE_ADDR,
            flags=I2C_M_RD,
            len=sizeof(buf),
            buf=buf
            )

        # Create C-based I2C struct to pass as ioctl() arg
        nmsgs = 2
        msgs = (i2c_msg * 2)(write_msg, read_msg)
        ioctl_arg = i2c_rdwr_ioctl_data(
            msgs=msgs,
            nmsgs=nmsgs
            )

        # ioctl() to do the I2C READ/WRITE
        ret = ioctl(self.fd, I2C_RDWR, ioctl_arg)
        if ret != 2:
            raise IOError('ioctl() failed to send to I2C messages ({})'.format(ret))

        # HW workaround.  See docstring.
        os.read(self.fd, 1)

        return string_at(read_msg.buf, read_msg.len)

    def forces(self):
        '''Returns a tuple of X, Y and Z forces.

        Forces are floats in units of `g` (for g-force), where the g-force is
        the gravitational force of the Earth.  An object in free-fall will
        measure 0 `g` in the direction that it is falling.  An object resting
        on a table will measure 1 `g` in the downward direction.  Thus, if the
        RaspberrySTEM is sitting flat and upright on a table, the return value
        should be close to (0.0, 0.0, 1.0).
        '''
        # Verify data is ready
        TRIES = 5
        for i in range(TRIES):
            if self._read(STATUS, 1)[0] & 0x0F == 0xF:
                break
            time.sleep(0.001)
        if i + 1 == TRIES:
            raise IOError('Accelerometer data is not available')

        data = self._read(OUT_X_MSB, 6)
        raw_forces = unpack('>hhh', data)

        # Convert raw forces (10-bit left aligned 2's complement data in an
        # unsigned short) to floats in units of 'g'.
        g_forces = [(raw_force>>6)/self.resolution for raw_force in raw_forces]

        # Part is on underside of board, this inverts the Y and Z axes.
        x, y, z = g_forces
        g_forces = x, -y, -z

        return g_forces

    def __del__(self):
        os.close(self.fd)

__all__ = ['Accel']
