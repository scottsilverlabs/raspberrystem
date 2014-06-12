#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

#define SPI_DEV "/dev/spidev0.0"

int spi;
unsigned char spiMode;
unsigned char bitsPerTrans;
unsigned int spiSpeed;

int startSPI(unsigned int speed, int mode){
	char *sMode;
	if(mode == 0){
		sMode = "/dev/spidev0.0";
	} else {
		sMode = "/dev/spidev0.1";
	}
	int err;
	spiMode = SPI_MODE_0;
	bitsPerTrans = 8;
	spiSpeed = 100000;
	spi = open(sMode,O_RDWR);
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
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)val,
		.len = len,
		.delay_usecs = 100,
	};
	int ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
return ret;
}
static PyObject *initSPI(PyObject *self, PyObject *args){
	unsigned int speed;
	int mode;
	if(!PyArg_ParseTuple(args, "Ii", &speed, &mode)){
		PyErr_SetString(PyExc_TypeError, "Not an unsigned int and int!");
		return NULL;
	}
	return Py_BuildValue("i",startSPI(speed, mode));
}
static PyObject *flush(PyObject *self, PyObject *args){
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
static PyObject *closeSPI(PyObject *self, PyObject *args){
	return Py_BuildValue("i", close(spi));
}
static PyMethodDef led_server_methods[] = {
	{"flush", flush, METH_VARARGS},
	{"initSPI", initSPI, METH_VARARGS},
	{"closeSPI", closeSPI, METH_NOARGS},
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

static int led_server_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int led_server_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}


static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "led_server",
        NULL,
        sizeof(struct module_state),
        led_server_methods,
        NULL,
        led_server_traverse,
        led_server_clear,
        NULL
};

#define INITERROR return NULL

PyObject *
PyInit_led_server(void)

#else
#define INITERROR return

void
initled_server(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("led_server", led_server_methods);
#endif

    if (module == NULL)
        INITERROR;
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("led_server.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
