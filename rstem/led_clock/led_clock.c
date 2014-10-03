/*
 * led_clock.c
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

// display current framebuffer during flush
int display_on_terminal = 0;
/*#if (display_on_terminal == 1)*/
/*    #include <ncurses.h>*/
/*    initscr();*/
/*#endif*/

#define DIM_OF_MATRIX 8
#define BITS_PER_PIXEL 4
#define MAX_MATRICES 50

// number of bytes in a matrix
#define NUM_BYTES_MATRIX ((DIM_OF_MATRIX*DIM_OF_MATRIX)/2)
#define bitstream_SIZE (num_matrices*NUM_BYTES_MATRIX)

#define COORDS_TO_INDEX(x, y) ((y)*container_width + (x))

#define SIGN(x) (((x) >= 0) ? 1 : -1)

int debug = 0;
#define Debug(args...) if (debug) {printf("led_clock: " args); printf("\n");}

int spi;
unsigned char spi_mode;
unsigned char bits_per_trans;
unsigned int spi_speed;
unsigned char data[5] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

unsigned char num_to_byte(int value, int dp) {
    unsigned char num = 0x00;
    if(value == 1) {
        num = 0b11111001;
    } else if(value == 2) {
        num = 0b10100100;
    } else if(value == 3) {
        num = 0b10110000;
    } else if(value == 4) {
        num = 0b10011001;
    } else if(value == 5) {
        num = 0b10010010;
    } else if(value == 6) {
        num = 0b10000010;
    } else if(value == 7) {
        num = 0b11111000;
    } else if(value == 8) {
        num = 0b10000000;
    } else if(value == 9) {
        num = 0b10011000;
    } else if(value == 0) {
        num = 0b11000000;
    }
    if(dp) {
        num &= 0b01111111;
    }
    return num;
}

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
//        .delay_usecs = 100,
    };
    int ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
    return ret;
}

int set_digit(int digit, int value, int dp) {
    if(digit == 1) {
        data[0] = num_to_byte(value, dp);
    } else if(digit == 2) {
        data[1] = num_to_byte(value, dp);
    } else if(digit == 3) {
        data[2] = num_to_byte(value, dp);
    } else if(digit == 4) {
        data[3] = num_to_byte(value, dp);
    }

    return 1;
}

int set_modifier(int colon, int apost) {
    unsigned char mod = 0;
    if(colon) {
        mod |= 0x06;
    }
    if(apost) {
        mod |= 0x01;
    }
    data[4] = mod;

    return 1;
}

// Python Wrappers =================================================

static PyObject *py_set_digit(PyObject *self, PyObject *args){
    int digit, value, dp;
    if(!PyArg_ParseTuple(args, "iii", &digit, &value, &dp)){
        PyErr_SetString(PyExc_TypeError, "Not three ints!");
        return NULL;
    }

    return Py_BuildValue("i", set_digit(digit, value, dp));
}

static PyObject *py_set_modifier(PyObject *self, PyObject *args){
    int colon, apost;
    if(!PyArg_ParseTuple(args, "ii", &colon, &apost)){
        PyErr_SetString(PyExc_TypeError, "Not an int and int!");
        return NULL;
    }

    return Py_BuildValue("i", set_modifier(colon, apost));
}

static PyObject *py_init_SPI(PyObject *self, PyObject *args){
    unsigned int speed;
    int mode;
    if(!PyArg_ParseTuple(args, "ki", &speed, &mode)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned long and int!");
        return NULL;
    }
    return Py_BuildValue("i", start_SPI(speed, mode));
}

static PyObject *py_flush(PyObject *self, PyObject *args) {
    return Py_BuildValue("i", write_bytes(spi, data, 5));
}

static PyMethodDef led_clock_methods[] = {
    {"init_SPI", py_init_SPI, METH_VARARGS, "Initialize the SPI with given speed and port."},
    {"digit", py_set_digit, METH_VARARGS, "Sets the given digit to the given value."},
    {"modifier", py_set_modifier, METH_VARARGS, "Controls the modifier LEDs."},
    {"flush", py_flush, METH_NOARGS, "Flushes data buffer."},
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

// static PyObject * error_out(PyObject *m) {
//     struct module_state *st = GETSTATE(m);
//     PyErr_SetString(st->error, "something bad happened");
//     return NULL;
// }

#if PY_MAJOR_VERSION >= 3

static int led_clock_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int led_clock_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}


static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "led_clock",
        NULL,
        sizeof(struct module_state),
        led_clock_methods,
        NULL,
        led_clock_traverse,
        led_clock_clear,
        NULL
};

#define INITERROR return NULL

PyObject *
PyInit_led_clock(void)

#else
#define INITERROR return

void initled_clock(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("led_clock", led_clock_methods);
#endif

    if (module == NULL)
        INITERROR;
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("led_clock.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
