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

static PyMethodDef mcp3002_methods[] = {
	{"read", readChannel, METH_VARARGS},
	{"initSPI", initSPI, METH_VARARGS},
	{"closeSPI", closeSPI, METH_VARARGS},
	{NULL, NULL}
};

struct module_state {
    PyObject *error;
};

#if PY_MAJOR_VERSION >= 3
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct module_state _state;
#endif

static PyObject *
error_out(PyObject *m) {
    struct module_state *st = GETSTATE(m);
    PyErr_SetString(st->error, "something bad happened");
    return NULL;
}

#if PY_MAJOR_VERSION >= 3

static int mcp3002_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int mcp3002_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}


static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "mcp3002",
        NULL,
        sizeof(struct module_state),
        mcp3002_methods,
        NULL,
        mcp3002_traverse,
        mcp3002_clear,
        NULL
};

#define INITERROR return NULL

PyObject *
PyInit_mcp3002(void)

#else
#define INITERROR return

void
initmcp3002(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("mcp3002", mcp3002_methods);
#endif

    if (module == NULL)
        INITERROR;
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("mcp3002.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
