#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

#define DIM_OF_MATRIX 8
#define SIZE_OF_PIXEL 4

// number of bytes in a matrix
#define NUM_BYTES_MATRIX ((DIM_OF_MATRIX*DIM_OF_MATRIX)/2)
#define BITSTREAM_SIZE (num_matrices*NUM_BYTES_MATRIX)

int spi;
unsigned char spiMode;
unsigned char bitsPerTrans;
unsigned int spiSpeed;

int main(){
    // testing purpose TODO remove
}

struct Matrix {
    int x_offset;
    int y_offset;
    int angle;
};

struct Matrix *LEDList;       // information on led matrix elements
unsigned int **frameBuffer;   // information on all pixels (physical or not)
unsigned char *bitStream;     // data given to SPI port
int num_matrices, container_width, container_height;

// SPI Stuff  =============================================

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

// ========================================================

int fill(unsigned int color){
    int y;
    for (y = 0; y < container_height; y++){
        int x;
        for (x = 0; x < container_width; x++){
            point(x, y, color);
        }
    }
    return 0;
}

// void convert_to_std_angle(int *x, int *y){
//     if (led.angle == 90){
//         int oldx = *x;
//         *x = *y;
//         *y = (PIXEL_HEIGHT - 1) - oldx;
//     } else if (led.angle == 180){
//         *x = (PIXEL_WIDTH - 1) - *x;
//         *y = (PIXEL_HEIGHT - 1) - *y;
//     } else if (led.angle == 270){
//         int oldy = *y;
//         *y = *x;
//         *x = (PIXEL_WIDTH - 1) - oldy;
//     }
// }


// int point_to_bitPos(int x, int y){
//
//     int mat_row = MAT_ROW(x,y);
//     // subtract off above matrix row and column so we can tread y relative to matrix row
//     y = (y - mat_row*DIM_OF_MATRIX);
//     // if on odd matrix row and zigzag enabled, we need to flip x and y coords
//     // (this allows us to treat x,y,mat_row,and mat_col as if zigzag == False)
//     if (mat_row % 2 == 1 && led.zigzag){
//         x = (DIM_OF_MATRIX*led.num_cols - 1) - x;
//         y = (DIM_OF_MATRIX - 1) - y;
//     }
//     // subtract off left matrix columns so we can treat x relative to matrix element
//     x = (x - MAT_COL(x,y)*DIM_OF_MATRIX);
//
//
//     // x and y now relative to matrix element
//     // get bitPos relative to matrix element
//     int bitPosCol = x*DIM_OF_MATRIX*SIZE_OF_PIXEL;
//     int bitPosColOffset = (DIM_OF_MATRIX - 1 - y)*SIZE_OF_PIXEL;
//     int bitPos = bitPosCol + bitPosColOffset;
//
//     // update bitPos to be absolute index of entire matrix
//     bitPos += MAT_INDEX(x,y)*NUM_BITS_MATRIX;
//
//     return bitPos;
// }

int point(int x, int y, unsigned int color) {
    frameBuffer[y][x] = color;
}

int line(int x1, int y1, int x2, int y2, unsigned int color){
    // TODO
    return 0;
}



int initFrameBufferandBitStream(){
    LEDList = (struct Matrix *) malloc(num_matrices*sizeof(struct Matrix));
    if (LEDList == 0){
        return -1;
    }
    frameBuffer = (unsigned int **) malloc(container_height*sizeof(unsigned int *));
    if (frameBuffer == 0){
        goto freeLEDList;
    }
    int i;
    // TODO: do a one dimensional array
    for (i = 0; i < container_height; i++){
        frameBuffer[i] = (unsigned int *) malloc(container_width*sizeof(unsigned int));
        if (frameBuffer[i] == 0){
            goto freeFrameBuffer;
        }
    }
    bitStream = (unsigned char *) malloc(num_matrices*NUM_BYTES_MATRIX);
    if (bitStream == 0){
        goto freeFrameBuffer;
    }

    return 0;

    // Clean up on malloc error
    freeFrameBuffer:
        for (i--; i >= 0; i--){
            free(frameBuffer[i]);
        }
        free(frameBuffer);
    freeLEDList:
        free(LEDList);
    PyErr_NoMemory();
    return -1;
}

// updates bitStream with current frame buffer
int update_bitStream(){
    int matrix_i;
    int bitStreamPos = 0;
    // loop through matrices in reverse order and append to bitstream
    for (matrix_i = (num_matrices - 1); matrix_i >= 0; matrix_i--){
        // place colors in bitStream based off of the angle specified
        if (LEDList[matrix_i].angle = 0){
            int x;
            for (x = 0; x < DIM_OF_MATRIX; x++){
                int y;
                for (y = (DIM_OF_MATRIX - 1); y >= 0; y -= 2){
                    bitStream[bitStreamPos++] = ((frameBuffer[y][x] & 0xF) << 4) | (frameBuffer[y+1][x] & 0xF);
                }
            }
        }
        if (LEDList[matrix_i].angle = 90){
            int y;
            for (y = 0; y < DIM_OF_MATRIX; y++){
                int x;
                for (x = 0; x < DIM_OF_MATRIX; x += 2){
                    bitStream[bitStreamPos++] = ((frameBuffer[y][x+1] & 0xF) << 4) | (frameBuffer[y][x] & 0xF);
                }
            }
        }
        if (LEDList[matrix_i].angle = 180){
            int x;
            for (x = (DIM_OF_MATRIX - 1); x >= 0; x--){
                int y;
                for (y = 0; y < DIM_OF_MATRIX; y += 2){
                    bitStream[bitStreamPos++] = ((frameBuffer[y+1][x] & 0xF) << 4) | (frameBuffer[y][x] & 0xF);
                }
            }
        }
        if (LEDList[matrix_i].angle = 0){
            int y;
            for (y = (DIM_OF_MATRIX - 1); y >= 0; y--){
                int x;
                for (x = (DIM_OF_MATRIX - 1); x >= 0; x -= 2){
                    bitStream[bitStreamPos++] = ((frameBuffer[y][x] & 0xF) << 4) | (frameBuffer[y][x+1] & 0xF);
                }
            }
        }
    }
}

// closes SPI port and frees all allocated memory
int closeAndFree(){
    int i;
    if (frameBuffer){
        for (i = 0; i < container_height; i++){
            free(frameBuffer[i]);
        }
    }
    free(frameBuffer);
    if (LEDList){
        free(LEDList);
    }
    if (bitStream){
        free(bitStream);
    }
    close(spi);
    return 0;
}


// Python Wrappers =================================================

static PyObject *pyInitMatrices(PyObject *self, PyObject *args){
    // TODO: no need to pass the LEDList over just set up the global variable here
    // RAWGGGGG!!!!
    PyObject *mat_list;  // the list object
    // grab mat_list and global variables
    if (!PyArg_ParseTuple(args, "O!iii", &PyList_Type, &mat_list, &num_matrices,
        &container_width, &container_height)){
        PyErr_SetString(PyExc_TypeError, "Invalid arguments.");
        return NULL;
    }
    int listSize = PyList_Size(mat_list);
    if (!PyList_Check(mat_list) || listSize < 0){
        PyErr_SetString(PyExc_TypeError, "Not a list");
        return NULL;
    }
    if (listSize % 3 != 0){
        PyErr_SetString(PyExc_ValueError, "List must be a multiple of 3.");
        return NULL;
    }
    // get LEDlist ready
    LEDList = (struct Matrix *) malloc((listSize/3)*sizeof(struct Matrix));
    if (!LEDList){
        PyErr_NoMemory();
        return NULL;
    }
    // iterate through list object and place items in LEDList
    int i;
    PyObject *xOffsetObj;
    PyObject *yOffsetObj;
    PyObject *angleObj;
    for (i = 0; i < listSize; i += 3){
        xOffsetObj = PyList_GetItem(mat_list, i);
        yOffsetObj = PyList_GetItem(mat_list, i + 1);
        angleObj = PyList_GetItem(mat_list, i + 2);
        if (!PyInt_Check(xOffsetObj) || !PyInt_Check(yOffsetObj) || !PyInt_Check(angleObj)){
            PyErr_SetString(PyExc_TypeError, "Non-integer was in the list.");
        }
        LEDList[i].x_offset = PyInt_AsLong(xOffsetObj);
        LEDList[i].y_offset = PyInt_AsLong(yOffsetObj);
        LEDList[i].angle = PyInt_AsLong(angleObj);
    }
    // initialize the framebuffer and bitstream
	return Py_BuildValue("i", initFrameBufferandBitStream());
}

static PyObject *pyFill(PyObject *self, PyObject *args){
    unsigned int color;
    if(!PyArg_ParseTuple(args, "I", &color)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned int!");
        return NULL;
    }
    if(fill(color) < 0){
        PyErr_SetString(PyExc_RuntimeError, "Something bad happned...");
    }
    return Py_BuildValue("i", 1);
}

static PyObject *pyLine(PyObject *self, PyObject *args){
    int x1, y1, x2, y2;
    unsigned int color;
	if(!PyArg_ParseTuple(args, "iiiiI", &x1, &y1, &x2, &y2, &color)){
		PyErr_SetString(PyExc_TypeError, "Not ints!");
		return NULL;
	}
	if(line(x1, y1, x2, y2, color) < 0){
	    PyErr_SetString(PyExc_RuntimeError, "Something bad happned...");
	}
	return Py_BuildValue("i", 1);
}

static PyObject *pyPoint(PyObject *self, PyObject *args){
    int x, y, color;
	if(!PyArg_ParseTuple(args, "iii", &x, &y, &color)){
		PyErr_SetString(PyExc_TypeError, "Not ints!");
		return NULL;
	}
	if(point(x,y,color) < 0){
	    PyErr_SetString(PyExc_RuntimeError, "Something bad happned...");
	}
	return Py_BuildValue("i", 1);
}


static PyObject *pyInitSPI(PyObject *self, PyObject *args){
	unsigned int speed;
	int mode;
	if(!PyArg_ParseTuple(args, "Ii", &speed, &mode)){
		PyErr_SetString(PyExc_TypeError, "Not an unsigned int and int!");
		return NULL;
	}
	return Py_BuildValue("i", startSPI(speed, mode));
}

static PyObject *pyFlush(PyObject *self, PyObject *args){
    update_bitStream();
    return Py_BuildValue("i", writeBytes(spi, bitStream, BITSTREAM_SIZE));
}

// static PyObject *flush(PyObject *self, PyObject *args){
// 	PyObject* seq;
// 	unsigned char *data;
// 	int size = 1;
// 	int index = 0;
// 	PyArg_ParseTuple(args, "O", &seq);
// 	if(!PyByteArray_Check(seq)){
// 		PyErr_SetString(PyExc_TypeError, "Not a bytearray");
// 		return NULL;
// 	}
// 	size = PyObject_Length(seq);
// 	data = PyByteArray_AsString(seq);
// return Py_BuildValue("i",writeBytes(spi, data, size));
// }

static PyObject *pyClose(PyObject *self, PyObject *args){
	return Py_BuildValue("i", closeAndFree());
}

static PyMethodDef led_driver_methods[] = {
	{"initSPI", pyInitSPI, METH_VARARGS, "Initialize the SPI with given speed and port."},
    {"initMatrices", pyInitMatrices, METH_VARARGS, "Initializes the give LED matrices in the list."},
    {"flush", pyFlush, METH_NOARGS, "Converts current frame buffer to a bistream and then sends it to SPI port."},
	{"close", pyClose, METH_NOARGS, "Closes the SPI and frees all memory."},
	{"point", pyPoint, METH_VARARGS, "Sets a point in the frame buffer."},
	{"line", pyLine, METH_VARARGS, "Sets a line from given source to destination."},
    {"fill", pyFill, METH_VARARGS, "Fills all matrices with the given color."},
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

static PyObject *
error_out(PyObject *m) {
    struct module_state *st = GETSTATE(m);
    PyErr_SetString(st->error, "something bad happened");
    return NULL;
}

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

void
initled_driver(void)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("led_driver", led_driver_methods);
#endif

    if (module == NULL)
        INITERROR;
    struct module_state *st = GETSTATE(module);

    st->error = PyErr_NewException("led_driver.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
