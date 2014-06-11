#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

#define SPI_DEV "/dev/spidev0.1"

int spi;
//int spiChannel;
unsigned char spiMode;
unsigned char bitsPerTrans;
unsigned int spiSpeed;

int startSPI(unsigned int speed, int spidev){
	char *sdev = "";
	if(spidev == 0){
		sdev = "/dev/spidev0.0";
	} else if (spidev == 1){
		sdev = "/dev/spidev0.1";
	} else {
		goto out;
	}
	int err;
	spiMode = 0;
	bitsPerTrans = 8;
	spiSpeed = speed;
	spi = open(sdev,O_RDWR);
	/*
	* spi mode
	*/
	err = ioctl(spi, SPI_IOC_WR_MODE, &spiMode);
	if (err < 0)
		goto out;

	err = ioctl(spi, SPI_IOC_RD_MODE, &spiMode);
	if (err < 0)
		goto out;

	/*
	* bits per word
	*/
	err = ioctl(spi, SPI_IOC_WR_BITS_PER_WORD, &bitsPerTrans);
	if (err < 0)
		goto out;

	/*
	* max speed hz
	*/
	err = ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, &spiSpeed);
	if (err < 0)
		goto out;

	out:
	    if (err < 0 && spi > 0)
	        close(spi);
return spi;
}

static PyObject *closeSPI(PyObject *self, PyObject *args){
	return Py_BuildValue("i", close(spi));
}

double writeByte(int dev, unsigned char val) {
	int ret;
	unsigned char tx[2];
	unsigned char rx[2];
	tx[0] = val;
	tx[1] = 0;
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)tx,
		.rx_buf = (unsigned long)rx,
		.len = 2,
	};
		ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
	unsigned int rd = (((rx[0] << 8) | rx[1]) & 0x3FF);
	return ((double) rd)/1024.0;
}

static PyObject *initSPI(PyObject *self, PyObject *args){
	unsigned int speed;
	int mode;
	if(!PyArg_ParseTuple(args, "Ii", &speed, &mode)) {
		PyErr_SetString(PyExc_TypeError, "Not a unsigned int and int!");
		return NULL;
	}
	PyObject *ret = Py_BuildValue("i", startSPI(speed, mode));
	return ret;
}

static PyObject *readChannel(PyObject *self, PyObject *args){
	int mode;
	unsigned char contByte;
	if(!PyArg_ParseTuple(args, "i", &mode)){
		PyErr_SetString(PyExc_TypeError, "Not an int!");
		return NULL;
	}
	if(mode == 0) {
		contByte = 0x60;
	} else if (mode == 1) {
		contByte = 0x70;
	} else if (mode == 2) {
		contByte = 0x40;
	} else if (mode == 3) {
		contByte = 0x50;
	}
	double val = writeByte(spi, contByte);
	//double val = 1024.0/((double) (((upper[0] << 8)&0x3)|(lower[0])));
	return Py_BuildValue("d", val);
}

static PyMethodDef spiMethods[] = {
	{"read", readChannel, METH_VARARGS},
	{"initSPI", initSPI, METH_VARARGS},
	{"closeSPI", closeSPI, METH_VARARGS}
};

void initmcp3002() {
	(void) Py_InitModule("mcp3002", spiMethods);
}
