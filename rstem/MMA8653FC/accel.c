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

int adapter_number = 0;
int addr = 0x1D;
unsigned char rawData[7];
unsigned char prescale = 0x01;
int accelData[3];
int file;
unsigned char int_enable = 0x00;
unsigned char int_pins = 0x00;

//By default the range is +- 4G
float range = 4.0;

int init_i2c(){
	adapter_number = adapter_number;
	char filename[20];
	snprintf(filename, 19, "/dev/i2c-%d", adapter_number);
	file = open(filename, O_RDWR);
	return file;
}

int set_slave(){
	return ioctl(file, I2C_SLAVE, addr);
}

int write_command(char reg, char value){
	return i2c_smbus_write_byte_data(file, reg, value);
}

static PyObject* init_accel(PyObject *self, PyObject *args) {
	int ret;
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
	ret = write_command(CTRL_REG1, prescale);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not initialize accel!");
                return NULL;
        }
	return Py_BuildValue("i", ret);
}

//Mode is 0 for free fall, 1 for motion detect
//mode pin
static PyObject * enable_freefall_motion(PyObject *self, PyObject *args){
	int mode, pin;
	if(!PyArg_ParseTuple(args, "ii", &mode, &pin)){
		PyErr_SetString(PyExc_TypeError, "Not two ints!");
		return NULL;
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

//debouce_mode thresh
static PyObject* set_freefall_motion_threshold(PyObject *self, PyObject *args){
	unsigned char debounce_mode;
	float f_thresh;
	unsigned char thresh;
	if(!PyArg_ParseTuple(args, "Bf", &debounce_mode, &f_thresh)){
		PyErr_SetString(PyExc_TypeError, "Not a byte and a float!");
		return NULL;
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

//Count
static PyObject* set_freefall_motion_debounce(PyObject *self, PyObject *args){
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

static PyObject * update_data(PyObject *self, PyObject *args){
	usleep(1000);
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
	float x = ((float) accelData[0])/(512.0/range);
	float y = ((float) accelData[1])/(512.0/range);
	float z = ((float) accelData[2])/(512.0/range);
	return Py_BuildValue("fff", x, y, z);
}


static PyObject * enable_tilt(PyObject *self, PyObject *args){
	int ret;
	int pin;
	unsigned char debounce;
	if(!PyArg_ParseTuple(args, "iB", &pin, &debounce)){
		PyErr_SetString(PyExc_TypeError, "Not an int and a byte!");
		return NULL;
	}
	int_enable |= (1 << 4);
	if(pin == 1){
		int_pins |= (1 << 4);
	} else {
		int_pins &= ~(1 << 4);
	}
	ret = write_command(CTRL_REG1, 0x00);
	if(ret < 0){
		PyErr_SetString(PyExc_IOError, "Could not enable tilt interrupt!");
		return NULL;
	}
	ret = write_command(CTRL_REG4, int_enable);
	if(ret < 0){
		PyErr_SetString(PyExc_IOError, "Could not enable tilt interrupt!");
		return NULL;
	}
	ret = write_command(CTRL_REG5, int_pins);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable tilt interrupt!");
                return NULL;
        }
        ret = write_command(PL_CFG, (1 << 7) | (1 << 6));
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable tilt interrupt!");
                return NULL;
        }
        ret = write_command(PL_COUNT, debounce);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable tilt interrupt!");
                return NULL;
        }
        ret = write_command(CTRL_REG1, prescale);
        if(ret < 0){
                PyErr_SetString(PyExc_IOError, "Could not enable tilt interrupt!");
                return NULL;
        }
	return Py_BuildValue("i", ret);
}


static PyObject * enable_data_ready(PyObject *self, PyObject *args){
	int pin;
	int ret;
	if(!PyArg_ParseTuple(args, "i", &pin)){
		PyErr_SetString(PyExc_TypeError, "Not an int!");
		return NULL;
	}
	if(pin != 1 & pin != 2){
		PyErr_SetString(PyExc_Exception, "Invalid interrupt pin!");
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

static PyObject * set_sample_rate_prescaler(PyObject *self, PyObject *args){
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

static PyObject * set_range(PyObject *self, PyObject *args){
	int ret;
	int range;
	if(!PyArg_ParseTuple(args, "i", &range)){
		PyErr_SetString(PyExc_TypeError, "Not an int!");
		return NULL;
	}
	if(range == 2){
		ret = write_command(XYZ_DATA_CFG, 0x00);
	} else if(range == 4){
		ret = write_command(XYZ_DATA_CFG, 0x01);
	} else if(range == 8){
		ret = write_command(XYZ_DATA_CFG, 0x02);
	} else {
		PyErr_SetString(PyExc_Exception, "Invalid range! (Valid: 2, 4, 8)");
		return NULL;
	}
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
	{"enable_tilt", enable_tilt, METH_VARARGS, "Enables tile interrupt on input pin with input debounce samples."},
	{"enable_data_ready", enable_data_ready, METH_VARARGS, "Enables the data ready interrupt on input pin."},
	{"set_sample_rate_prescaler", set_sample_rate_prescaler, METH_VARARGS, "Sets the prescalers for the sample rate"},
	{"set_range", set_range, METH_VARARGS, "Sets the range of the accelerometer"},
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

static int accel__traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int accel_clear(PyObject *m) {
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



