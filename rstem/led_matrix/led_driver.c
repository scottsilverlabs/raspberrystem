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

#define MAX_MATRICES 50

int spi;
unsigned char spi_mode;
unsigned char bits_per_trans;
unsigned int spi_speed;


// SPI  =============================================

int start_spi(unsigned long speed, int mode){
    char *sMode;
    if (spi) {
        close(spi);
    }
    if(mode == 0){
        sMode = "/dev/spidev0.0";
    } else {
        sMode = "/dev/spidev0.1";
    }
    int err;
    spi_mode = SPI_MODE_0;
    bits_per_trans = 8;
    spi_speed = speed;
    spi = open(sMode, O_RDWR);

    err = ioctl(spi, SPI_IOC_WR_MODE, &spi_mode);
    if (err < 0) goto out;

    err = ioctl(spi, SPI_IOC_RD_MODE, &spi_mode);
    if (err < 0) goto out;

    err = ioctl(spi, SPI_IOC_WR_BITS_PER_WORD, &bits_per_trans);
    if (err < 0) goto out;

    err = ioctl(spi, SPI_IOC_WR_MAX_SPEED_HZ, &spi_speed);
    if (err < 0) goto out;

out:
    if (err < 0 && spi > 0)
        close(spi);
    return spi;
}

int rw_bytes(int dev, char * val, char * buff, int len){
    struct spi_ioc_transfer tr = {
        .tx_buf = (unsigned long)val,
        .rx_buf = (unsigned long)buff,
        .len = len
    };
    int ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
    return ret;
}

// Python Wrappers =================================================


static PyObject *py_init_spi(PyObject *self, PyObject *args){
    unsigned int speed;
    int mode;
    int ret;
    if(!PyArg_ParseTuple(args, "ki", &speed, &mode)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned long and int!");
        return NULL;
    }
    ret = start_spi(speed, mode);
    if (ret < 0) {
        PyErr_SetString(PyExc_IOError, "Failed to init SPI port.");
        return NULL;
    }
    return Py_BuildValue("");
}   

static PyObject *py_send(PyObject *self, PyObject *args){
    char *s;
    int len;
    if(!PyArg_ParseTuple(args, "y#", &s, &len)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned int!");
        return NULL;
    }
    if (rw_bytes(spi, s, s, len) < 0) {
        PyErr_SetString(PyExc_IOError, "Failed to read/write LED Matrices via SPI.");
        return NULL;
    }
    return Py_BuildValue("y#", s, len);
}

static PyMethodDef led_driver_methods[] = {
    {"init_spi", py_init_spi, METH_VARARGS, "Initialize the SPI port."},
    {"send", py_send, METH_VARARGS, "Sends bytes via SPI port."},
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
