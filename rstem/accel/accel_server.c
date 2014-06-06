#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

#define SPI_DEV "/dev/spidev0.0"

int spi;
unsigned char spiMode;
unsigned char bitsPerTrans;
unsigned int spiSpeed;

int startSPI(unsigned int speed){
	int err;
	spiMode = SPI_MODE_0;
	bitsPerTrans = 8;
	spiSpeed = speed;
	spi = open(SPI_DEV,O_RDWR);
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

int writeByte(int dev, unsigned char *val, unsigned char *rx) {
	int ret;
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)val,
		.rx_buf = (unsigned long)rx,
		.len = 1,
	};
		ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
return ret;
}

static PyObject *initSPI(PyObject *self, PyObject *args){
	unsigned int speed;
	if(!PyArg_ParseTuple(args, "I", &speed)) {
		PyErr_SetString(PyExc_TypeError, "Not a unsigned int!");
		return NULL;
	}
	PyObject *ret = Py_BuildValue("i", startSPI(speed));
	return ret;
}

static PyObject *WRByte(PyObject *self, PyObject *args){
	unsigned char data[1];
	unsigned char rx[1];
	unsigned char b;
	if(!PyArg_ParseTuple(args, "b", &b)) {
		PyErr_SetString(PyExc_TypeError, "Not a byte!");
	}
	data[0] = b;
	if(writeByte(spi, data, rx) < 0) {
		PyErr_SetString(PyExc_RuntimeError, "Transfer failed!");
		return NULL;
	}
	PyObject *retByte = Py_BuildValue("b", rx[0]);
//	Py_INCREF(retByte);
	return retByte;
}

static PyMethodDef spiMethods[] = {
	{"write", WRByte, METH_VARARGS},
	{"initSPI", initSPI, METH_VARARGS},
	{"closeSPI", closeSPI, METH_VARARGS}
};

void initaccel() {
	(void) Py_InitModule("accel", spiMethods);
}
