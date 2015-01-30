/*
 * led_driver.c
 *
 * Copyright (c) 2014, Scott Silver Labs, LLC.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * This code originally used the SPI testing utility included with Linux as a
 * reference.
 */


#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>
#include <numpy/arrayobject.h>

#define MAX_MATRICES 50

int spi;
unsigned char spi_mode;
unsigned char bits_per_trans;
unsigned int spi_speed;


struct Matrix {
    int x_offset;
    int y_offset;
    int angle;
};

struct Matrix *led_list;       // information on led matrix elements
PyObject *numpy_array = NULL;  // if null we are using original framebuffer
int num_matrices, container_width, container_height;

// SPI Stuff  =============================================

int start_SPI(unsigned long speed, int mode){
	char *sMode;
	if(mode == 0){
		sMode = "/dev/spidev0.0";
	} else {
		sMode = "/dev/spidev0.1";
	}
	int err;
	spi_mode = SPI_MODE_0;
	bits_per_trans = 8;
	spi_speed = speed;
	spi = open(sMode,O_RDWR);
	/*
	* spi mode
	*/
	err = ioctl(spi, SPI_IOC_WR_MODE, &spi_mode);
	if (err < 0)
		goto out;

	err = ioctl(spi, SPI_IOC_RD_MODE, &spi_mode);
	if (err < 0)
		goto out;

	/*
	* bits per word
	*/
	err = ioctl(spi, SPI_IOC_WR_BITS_PER_WORD, &bits_per_trans);
	if (err < 0)
		goto out;

	/*
	* max speed hz
	*/
	err = ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, &spi_speed);
	if (err < 0)
		goto out;

	out:
	    if (err < 0 && spi > 0)
	        close(spi);
        return spi;
}

int write_bytes(int dev, unsigned char* val, int len) {
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)val,
		.len = len,
//		.delay_usecs = 100,
	};
	int ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
	return ret;
}

// memory commands ===========================================

int rw_bytes(int dev, unsigned char* val, unsigned char* buff, int len){
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)val,
		.rx_buf = (unsigned long)buff,
		.len = len
	};
	int ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
	return ret;
}

// led_driver commands =======================================

int num_of_matrices(void){
    // spam display with zeros to ensure its empty
	unsigned char* rx = (unsigned char*) malloc(32);
	unsigned char* tran = (unsigned char*) malloc(32);
	memset(rx, 0, 32);
	memset(tran, 0, 32);
	int i = 0;
	for(i = 0; i < MAX_MATRICES; i++){
		write_bytes(spi, tran, 32);
	}
	// send a high through and wait for response
	tran[0] = 0xFF;
	int count = 0;
	int ret = 0;
	while(rx[0] != 0xFF && count < 10){
		ret = rw_bytes(spi, tran, rx, 32);
		count++;
	}
	free(rx);
	free(tran);
	if(ret < 0 || count > 9){
		return -1;
	} else {
		tran = (unsigned char*) malloc(32*(count-1));
		memset(tran, 0, 32*(count - 1));
		ret = write_bytes(spi, tran, 32*(count - 1));
		free(tran);
		return count - 1;
	}
}


// Python Wrappers =================================================

static PyObject *py_num_of_matrices(PyObject *self, PyObject *args){
	int ret = num_of_matrices();
	if(ret < 0){
		PyErr_SetString(PyExc_IOError, "Number of matrices out of valid range (Valid: 1-8)");
		return NULL;
	}
	return Py_BuildValue("i", ret);
}

static PyObject *py_init_matrices(PyObject *self, PyObject *args){
    PyObject *mat_list;  // the list object
    // grab mat_list and global variables
    if (!PyArg_ParseTuple(args, "O!iii", &PyList_Type, &mat_list, &num_matrices,
        &container_width, &container_height)){
        PyErr_SetString(PyExc_TypeError, "Invalid arguments.");
        return NULL;
    }
    // get led_list ready
    led_list = (struct Matrix *) malloc((num_matrices)*sizeof(struct Matrix));
    if (led_list == 0){
        PyErr_NoMemory();
        return NULL;
    }
    memset(led_list, '\0', (num_matrices)*sizeof(struct Matrix));
    // iterate through list object and place items in led_list
    int i;
    for (i = 0; i < num_matrices; i++){
        int x_offset, y_offset;
        int angle = 0;  // set angle to be 0 by default if not changed in tuple
        if (!PyArg_ParseTuple(PyList_GetItem(mat_list, i), "ii|i", &x_offset, &y_offset, &angle)){
            PyErr_SetString(PyExc_TypeError, "Tuple not correct.");
            return NULL;
        }
        led_list[i].x_offset = x_offset;
        led_list[i].y_offset = y_offset;
        led_list[i].angle = angle;
    }
    // initialize the framebuffer and bitstream
    return Py_BuildValue("i", 0);
}

static PyObject *py_init_SPI(PyObject *self, PyObject *args){
	unsigned int speed;
	int mode;
	if(!PyArg_ParseTuple(args, "ki", &speed, &mode)){
		PyErr_SetString(PyExc_TypeError, "Not an unsigned long and int!");
		return NULL;
	}
	import_array();
	return Py_BuildValue("i", start_SPI(speed, mode));
}   

static PyObject *py_flush2(PyObject *self, PyObject *args){
    const char *s;
    int len;
    if(!PyArg_ParseTuple(args, "s#", &s, &len)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned int!");
        return NULL;
    }
    int i;
    for (i = 0; i < len; i++) {
        printf("%02X ", s[i]);
    }
    printf("\n");
    return Py_BuildValue("i", write_bytes(spi, s, len));
}

static PyMethodDef led_driver_methods[] = {
	{"init_SPI", py_init_SPI, METH_VARARGS, "Initialize the SPI with given speed and port."},
	{"init_matrices", py_init_matrices, METH_VARARGS, "Initializes the give LED matrices in the list."},
	{"flush2", py_flush2, METH_VARARGS, "Converts current frame buffer to a bistream and then sends it to SPI port."},
	{"detect", py_num_of_matrices, METH_NOARGS, "Returns the number of matrices connected"},
	{NULL, NULL, 0, NULL}  /* Sentinal */
};


// Python Setup Magic, don't touch! =====================

struct module_state {
    PyObject *error;
};

#if PY_MAJOR_VERSION >= 3
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct module_state _state;
#endif

#if PY_MAJOR_VERSION >= 3

static int led_driver_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int led_driver_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}


static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "led_driver",
        NULL,
        sizeof(struct module_state),
        led_driver_methods,
        NULL,
        led_driver_traverse,
        led_driver_clear,
        NULL
};

#define INITERROR return NULL

PyObject *
PyInit_led_driver(void)

#else
#define INITERROR return

void initled_driver(void)
#endif
{
    struct module_state *st;

#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("led_driver", led_driver_methods);
#endif

    if (module == NULL)
        INITERROR;

    st = GETSTATE(module);

    st->error = PyErr_NewException("led_driver.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
