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

int startSPI(){
	int err;
	spiMode = SPI_MODE_0;
	bitsPerTrans = 8;
	spiSpeed = 250000;
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

int writeBytes(int dev, unsigned char* val, int len) {
	int i = len;
	int ret = 1;
	for(i = 0; i < len; i++){
	unsigned char data[1];
	data[0] = val[i];
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)data,
		.len = 1,
	};
	ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
	usleep(10);
	}
return ret;
}
static PyObject *initSPI(PyObject *self, PyObject *args){
	return Py_BuildValue("i",startSPI());
}
static PyObject *flush(PyObject *self, PyObject *args){
//	startSPI();
	PyObject* seq;
	unsigned char *data;
	int size = 1;
	int index = 0;
	PyArg_ParseTuple(args, "O", &seq);
	if(!PyByteArray_Check(seq)){
		PyErr_SetString(PyExc_TypeError, "Not a bytearray");
		return NULL;
	}
	size = PyObject_Length(seq);
	data = PyByteArray_AsString(seq);
return Py_BuildValue("i",writeBytes(spi, data, size));
}

static PyMethodDef spiMethods[] = {
	{"flush", flush, METH_VARARGS},
	{"initSPI", initSPI, METH_VARARGS}
};

void initled_server() {
	(void) Py_InitModule("led_server", spiMethods);
}
