/*
 * accel.c
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
#include <linux/i2c-dev.h>
#include <fcntl.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <math.h>

#define STATUS 0x00
#define OUT_X_MSB 0x01
#define XYZ_DATA_CFG 0x0E

#define CTRL_REG1 0x2A
#define CTRL_REG2 0x2B
#define CTRL_REG3 0x2C
#define CTRL_REG4 0x2D
#define CTRL_REG5 0x2E

#define DR0 3
#define DR1 4
#define DR2 5

#define FF_MT_CFG 0x15
#define FF_MT_SRC 0x16
#define FF_MT_THS 0x17
#define FF_MT_COUNT 0x18

#define PL_STATUS 0x10
#define PL_CFG 0x11
#define PL_COUNT 0x12
#define PL_BF_ZCOMP 0x13
#define PL_THS_REG 0x14


/*
    Module Data ==========================================
*/
int adapter_number = 0;
int addr = 0x1D;
unsigned char rawData[7];
unsigned char prescale = 0x01;
int accelData[3];
int file;
unsigned char int_enable = 0x00;
unsigned char int_pins = 0x00;
int rad = 0;
//By default the range is +- 4G
double range = 4.0;

/*
    C Functions ===========================================
*/

//Returns degree representation of radians
double rad2deg(double x)
{
    return x*180.0/3.141592654;
}

//Initialize i2c
int init_i2c()
{
    char filename[20];
    snprintf(filename, sizeof(filename), "/dev/i2c-%d", adapter_number);
    file = open(filename, O_RDWR);
    return file;
}

//Set accel as slave
int set_slave()
{
    return ioctl(file, I2C_SLAVE, addr);
}

//Write command "value" to "reg"
int write_command(char reg, char value)
{
    return i2c_smbus_write_byte_data(file, reg, value);
}

/*
    Python C Bindings =====================================
*/

//Initialize accelerometer
static PyObject* init_accel(PyObject *self, PyObject *args)
{
    int ret;
    if(!PyArg_ParseTuple(args, "i", &adapter_number)){
        PyErr_SetString(PyExc_TypeError, "Not an int!");
        return NULL;
    }
    if(adapter_number != 0 && adapter_number != 1){
        PyErr_SetString(PyExc_IOError, "Not a valid I2C bus!");
        return NULL;
    }
    ret = init_i2c();
    if(ret < 0){
        PyErr_SetString(PyExc_IOError, "Could not initialize accel!");
        return NULL;
    }
    ret = set_slave();
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not initialize accel!");
                return NULL;
        }
    ret = write_command(CTRL_REG1, 0x00);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not initialize accel!");
                return NULL;
        }
    ret = write_command(XYZ_DATA_CFG, 0x01);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not initialize accel!");
                return NULL;
        }
    ret = write_command(CTRL_REG2, (1 << 4) | (1 << 3) | (1 << 1) | 1);
    if(ret < 0) {
        PyErr_SetString(PyExc_IOError, "Could not initialize accel!");
        return NULL;
    }
    ret = write_command(CTRL_REG1, prescale);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not initialize accel!");
                return NULL;
        }
    return Py_BuildValue("i", ret);
}
//Selects mode between degrees and radians
static PyObject *use_radians(PyObject *self, PyObject *args)
{
    if(!PyArg_ParseTuple(args, "i", &rad)){
        PyErr_SetString(PyExc_TypeError, "Not a boolean!");
        return NULL;
    }
    if(rad != 0){
        rad = 1;
    }
    return Py_BuildValue("i", rad);
}

//Mode is 0 for free fall, 1 for motion detect
static PyObject * enable_freefall_motion(PyObject *self, PyObject *args)
{
    int mode, pin;
    if(!PyArg_ParseTuple(args, "ii", &mode, &pin)){
        PyErr_SetString(PyExc_TypeError, "Not two ints!");
        return NULL;
    }
    if(pin != 1 && pin !=2){
        PyErr_SetString(PyExc_Exception, "Not a pin!");
    }
    int_enable |= (1 << 2);
    int ret;
    ret = write_command(CTRL_REG1, 0x00);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable interrupt!");
                return NULL;
        }
    ret = write_command(CTRL_REG3, 2);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable interrupt!");
                return NULL;
        }
    ret = write_command(CTRL_REG4, int_enable);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable interrupt!");
                return NULL;
        }
    unsigned char config = (1 << 5) | (1 << 4) | (1 << 3);
    if(pin == 1){
        int_pins |= (1 << 2);
    } else {
        int_pins &= ~(1 << 2);
    }
    ret = write_command(CTRL_REG5, int_pins);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable interrupt!");
                return NULL;
        }
    if(mode == 0){
        write_command(FF_MT_CFG, config);
            if(ret < 0){
                    PyErr_SetString(PyExc_IOError, "Could not enable interrupt!");
                    return NULL;
            }
    } else {
        ret = write_command(FF_MT_CFG, config | (1 << 6));
            if(ret < 0){
                    PyErr_SetString(PyExc_IOError, "Could not enable interrupt!");
                    return NULL;
            }
    }
    ret = write_command(CTRL_REG1, prescale);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable interrupt!");
                return NULL;
        }
    return Py_BuildValue("i", ret);
}

//debounce mode: 1 = decrement counter when below threshold
//             : 0 = clear counter when below threshold
//Threshold is a floating point number in Gs
static PyObject* set_freefall_motion_threshold(PyObject *self, PyObject *args)
{
    unsigned char debounce_mode;
    float f_thresh;
    unsigned char thresh;
    if(!PyArg_ParseTuple(args, "Bf", &debounce_mode, &f_thresh)){
        PyErr_SetString(PyExc_TypeError, "Not a byte and a float!");
        return NULL;
    }
    if(f_thresh > 8){
        PyErr_SetString(PyExc_Exception, "Not a valid range! (Valid: 0-8)");
        return NULL;
    }
    if(debounce_mode != 1 && debounce_mode != 0){
        PyErr_SetString(PyExc_Exception, "Not a valid debounce mode! (Valid: 1 0)");
    }
    thresh = (unsigned char) ((f_thresh/8.0)*127.0);
    int ret;
    ret = write_command(CTRL_REG1, 0x00);
    if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not set threshold!");
                return NULL;
        }
    ret = write_command(FF_MT_THS, ((debounce_mode & 0x01) << 8) | (thresh & 0x7F));
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not set threshold!");
                return NULL;
        }
    ret = write_command(CTRL_REG1, prescale);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not set threshold!");
                return NULL;
        }
    return Py_BuildValue("i", ret);
}

//Sets how many samples are required to trigger intterupt
static PyObject* set_freefall_motion_debounce(PyObject *self, PyObject *args)
{
    unsigned char counts;
    if(!PyArg_ParseTuple(args, "B", &counts)){
        PyErr_SetString(PyExc_TypeError, "Not a byte!");
        return NULL;
    }
    int ret;
    ret = write_command(CTRL_REG1, 0x00);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not set debounce!");
                return NULL;
        }
    ret = write_command(FF_MT_COUNT, counts);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not set debounce!");
                return NULL;
        }
    ret = write_command(CTRL_REG1, prescale);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not set debounce!");
                return NULL;
        }
    return Py_BuildValue("i", ret);
}

//Grab new data from device and give it to python
static PyObject * update_data(PyObject *self, PyObject *args)
{
    int ret;
    ret = i2c_smbus_read_i2c_block_data(file, 0x00, 7, rawData);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not update data!");
                return NULL;
        }
    int i;
    for(i = 0; i < 3; i++){
        accelData[i] = (int) ((rawData[2*i+1] << 2) | ((rawData[2*i+2] >> 6) & 0x03));
        if(accelData[i] > 1024/2) {
            accelData[i] -= 1025;
        }
    }
    double x = ((double) accelData[0])/(512.0/range);
    double y = ((double) accelData[1])/(512.0/range);
    double z = ((double) accelData[2])/(512.0/range);
    return Py_BuildValue("ddd", x, y, z);
}

//Grab new angles and give it to python
static PyObject * angles(PyObject *self, PyObject *args)
{
    int ret = i2c_smbus_read_i2c_block_data(file, 0x00, 7, rawData);
    if(ret < 0){
        PyErr_SetString(PyExc_IOError, "Could not update data!");
        return NULL;
    }
    int i;
        for(i = 0; i < 3; i++){
                accelData[i] = (int) ((rawData[2*i+1] << 2) | ((rawData[2*i+2] >> 6) & 0x03));
                if(accelData[i] > 1024/2) {
                        accelData[i] -= 1025;
                }
        }
        double x = ((double) accelData[0])/(512.0/range);
        double y = ((double) accelData[1])/(512.0/range);
        double z = ((double) accelData[2])/(512.0/range);

    double elevation = atan2(z, sqrt(x*x + y*y));
    double roll = atan2(x, sqrt(z*z + y*y));
    double pitch = atan2(y, sqrt(z*z + x*x));

    if(rad == 0){
        elevation = rad2deg(elevation);
        roll = rad2deg(roll);
        pitch = rad2deg(pitch);
    }

    return Py_BuildValue("ddd", roll, pitch, elevation);
}

//Enable data ready intterupt on given pin
static PyObject * enable_data_ready(PyObject *self, PyObject *args)
{
    int pin;
    int ret;
    if(!PyArg_ParseTuple(args, "i", &pin)){
        PyErr_SetString(PyExc_TypeError, "Not an int!");
        return NULL;
    }
    if(pin != 1 & pin != 2){
        PyErr_SetString(PyExc_Exception, "Invalid interrupt pin! (Valid: 1 2)");
        return NULL;
    }
    int_enable |= 1;
    if(pin == 1){
        int_pins |= 1;
    } else {
        int_pins &= ~1;
    }
    ret = write_command(CTRL_REG1, 0x00);
    if(ret < 0){
        PyErr_SetString(PyExc_IOError, "Could not enable data interrupt!");
        return NULL;
    }
    ret = write_command(CTRL_REG4, int_enable);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable data interrupt!");
                return NULL;
        }
    ret = write_command(CTRL_REG5, int_pins);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable data interrupt!");
                return NULL;
        }
    ret = write_command(CTRL_REG1, prescale);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable data interrupt!");
                return NULL;
        }
    return Py_BuildValue("i", ret);
}

//Sets sample rate prescaler, sample rate = 800hz/prescaler
static PyObject * set_sample_rate_prescaler(PyObject *self, PyObject *args)
{
    int rate;
    int ret;
    if(!PyArg_ParseTuple(args, "i", &rate)){
        PyErr_SetString(PyExc_TypeError, "Not an int!");
        return NULL;
    }
    if(rate == 1){
        prescale = 0x01;
    } else if(rate == 2){
                prescale = (1 << DR0) | 1;
        } else if(rate == 4){
                prescale = (1 << DR1) | 1;
    } else if(rate == 8){
                prescale = (1 << DR0) | (1 << DR1) | 1;
    } else if(rate == 16){
                prescale = (1 << DR2) | 1;
    } else if(rate == 64){
                prescale = (1 << DR2) | (1 << DR0) | 1;
    } else if(rate == 128){
                prescale = (1 << DR2) | (1 << DR1) | 1;
    } else if(rate == 512){
                prescale = (1 << DR2) | (1 << DR1) | (1 << DR0) | 1;
    } else {
        PyErr_SetString(PyExc_Exception, "Invalid prescaler! (Valid: 1, 2, 4, 8, 16, 64, 128, 512)");
        return NULL;
    }
    ret = write_command(CTRL_REG1, prescale);
    if(ret < 0){
        PyErr_SetString(PyExc_Exception, "Could not set prescaler!");
        return NULL;
    }
    return Py_BuildValue("i", ret);
}

//Sets full scale range of accelerometer
static PyObject * set_range(PyObject *self, PyObject *args)
{
    int ret;
    int in_range;
    if(!PyArg_ParseTuple(args, "i", &in_range)){
        PyErr_SetString(PyExc_TypeError, "Not an int!");
        return NULL;
    }
    ret = write_command(CTRL_REG1, 0x00);
    if(ret < 0){
        PyErr_SetString(PyExc_IOError, "Failed to set range!");
        return NULL;
    }
    if(in_range == 2){
        range = 2;
        ret = write_command(XYZ_DATA_CFG, 0x00);
    } else if(in_range == 4){
        range = 4;
        ret = write_command(XYZ_DATA_CFG, 0x01);
    } else if(in_range == 8){
        range = 8;
        ret = write_command(XYZ_DATA_CFG, 0x02);
    } else {
        PyErr_SetString(PyExc_Exception, "Invalid range! (Valid: 2, 4, 8)");
        return NULL;
    }
    if(ret < 0){
        PyErr_SetString(PyExc_IOError, "Failed to set range!");
        return NULL;
    }
    ret = write_command(CTRL_REG1, prescale);
    if(ret < 0){
        PyErr_SetString(PyExc_IOError, "Failed to set range!");
        return NULL;
    }
    return Py_BuildValue("i", ret);
}

static PyMethodDef accel_methods[] = {
    {"init", init_accel, METH_VARARGS, "Initializes accel on I2C bus."},
    {"enable_freefall_motion", enable_freefall_motion, METH_VARARGS, "Initializes the freefall/motion interrupts with the mode (0 for freefall 1 for motion) and the pin it will be on."},
    {"read", update_data, METH_NOARGS, "Updates and returns accelerometer data."},
    {"freefall_motion_threshold", set_freefall_motion_threshold, METH_VARARGS, "Sets debounce mode and threshold in Gs"},
    {"freefall_motion_debounce", set_freefall_motion_debounce, METH_VARARGS, "Sets number of debounce counts for interrupt to fire."},
    {"enable_data_ready", enable_data_ready, METH_VARARGS, "Enables the data ready interrupt on input pin."},
    {"set_sample_rate_prescaler", set_sample_rate_prescaler, METH_VARARGS, "Sets the prescalers for the sample rate."},
    {"set_range", set_range, METH_VARARGS, "Sets the range of the accelerometer."},
    {"angles", angles, METH_NOARGS, "Returns pitch, roll, and yaw."},
    {"use_radians", use_radians, METH_VARARGS, "Sets mode between radians or degrees."},
    {NULL, NULL, 0, NULL} // Sentinal
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

static int accel_traverse(PyObject *m, visitproc visit, void *arg)
{
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int accel_clear(PyObject *m)
{
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}


static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "accel",
        NULL,
        sizeof(struct module_state),
        accel_methods,
        NULL,
        accel_traverse,
        accel_clear,
        NULL
};

#define INITERROR return NULL

PyObject *
PyInit_accel(void)

#else
#define INITERROR return

void
initaccel(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("accel", accel_methods);
#endif

    if (module == NULL)
        INITERROR;
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("accel.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}



