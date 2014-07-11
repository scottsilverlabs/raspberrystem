#!/usr/bin/env python
import smbus
import time
accel = smbus.SMBus(0)

addr = 0x1D

CTRL_REG1 = 0x2A
XYZ_DATA_CFG = 0x0E

data = [None]*7
accelData = [None]*3

def command(com, data):
	accel.write_byte_data(addr, com, data)

def init():
	command(CTRL_REG1, 0x01)
	time.sleep(10.0/1000.0)
	command(XYZ_DATA_CFG, 0x01)
	time.sleep(1.0/1000.0)
	command(CTRL_REG1, 0x01)
	time.sleep(1.0/1000.0)

def read():
	global data
#	accel.write_byte(addr, 0x01)
#	time.sleep(1.0/1000.0)
#	for i in range(7):
#		data[i] = accel.read_byte(addr)
#		time.sleep(1.0/1000.0)
	data = accel.read_i2c_block_data(addr, 0x01, 7)
	for i in range(3):
		accelData[i] = (data[2*i+1] << 2) + (data[2*i+2] & 0x3)
		if accelData[i] > 1024/2:
			accelData[i] = accelData[i] - 1024

init()
while True:
	read()
	print(accelData)
	time.sleep(100.0/1000.0)
