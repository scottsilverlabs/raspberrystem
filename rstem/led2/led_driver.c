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

#define DIM_OF_MATRIX 8
#define BITS_PER_PIXEL 4

// number of bytes in a matrix
#define NUM_BYTES_MATRIX ((DIM_OF_MATRIX*DIM_OF_MATRIX)/2)
#define bitstream_SIZE (num_matrices*NUM_BYTES_MATRIX)

#define SIGN(x) (((x) >= 0) ? 1 : -1)

int debug = 0;
#define Debug(args...) if (debug) {printf("LED_DRIVER: " args); printf("\n");}

// display current framebuffer during flush
int display_on_terminal = 0;

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
unsigned int **framebuffer;   // information on all pixels (physical or not)
unsigned char *bitstream;     // data given to SPI port
int num_matrices, container_width, container_height;

// SPI Stuff  =============================================

int start_SPI(unsigned int speed, int mode){
	char *sMode;
	if(mode == 0){
		sMode = "/dev/spidev0.0";
	} else {
		sMode = "/dev/spidev0.1";
	}
	int err;
	spi_mode = SPI_MODE_0;
	bits_per_trans = 8;
	spi_speed = 100000;
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
		.delay_usecs = 100,
	};
	int ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
    return ret;
}

// led_driver commands =======================================

int point(int x, int y, unsigned int color) {
    Debug("Setting point at (%d,%d) with color %d", x, y, color);
    if (x >= container_width || x < 0 || y >= container_height || y < 0)
        return -1;
    framebuffer[x][y] = color;
    return 0;
}

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


int line(int x1, int y1, int x2, int y2, unsigned int color){
    int dx = abs(x2 - x1);
    int dy = abs(y2 - y1);
    int sx = (x1 < x2) ? 1 : -1;
    int sy = (y1 < y2) ? 1 : -1;
    int err = dx - dy;
    Debug("dx = %d, dy = %d, sx = %d, sy = %d, err = %d", dx, dy, sx, sy, err);
    while (1) {
        Debug(" x1, y1 = %d,%d   err = %d", x1, y1, err);
        point(x1, y1, color);
        if ((x1 == x2 && y1 == y2) || x1 >= container_width || y1 >= container_height)
            break;
        int e2 = 2*err;
        if (e2 > -dy) {
            err -= dy;
            x1 += sx;
        }
        if (e2 < dx) {
            err += dx;
            y1 += sy;
        }
    }
    return 0;
}



int init_framebuffer_and_bitstream(void){
    Debug("Initializing framebuffer");
    framebuffer = (unsigned int **) malloc(container_width*sizeof(unsigned int *));
    if (framebuffer == 0){
        Debug("Error mallocing framebuffer");
        goto freeLEDList;
    }
    int i;
    for (i = 0; i < container_width; i++){
        Debug("Initializing framebuffer[%d]", i);
        framebuffer[i] = (unsigned int *) malloc(container_height*sizeof(unsigned int));
        if (framebuffer[i] == 0){
            Debug("Error mallocing framebuffer[%d]", i);
            goto freeframebuffer;
        }
        memset(framebuffer[i], 0, container_height*sizeof(unsigned int));
    }
    Debug("Initializing bitstream");
    bitstream = (unsigned char *) malloc(num_matrices*NUM_BYTES_MATRIX);
    if (bitstream == 0){
        Debug("Error mallocing bitstream");
        goto freeframebuffer;
    }
    memset(bitstream, '\0', num_matrices*NUM_BYTES_MATRIX);
    return 0;

    // Clean up on malloc error
    freeframebuffer:
        for (i--; i >= 0; i--){
            free(framebuffer[i]);
        }
        free(framebuffer);
    freeLEDList:
        free(led_list);
    PyErr_NoMemory();
    return -1;
}

// updates bitstream with current frame buffer
int update_bitstream(void){
    Debug("Updating bitSream");
    int matrix_i;
    int bitstream_pos = 0;
    // loop through matrices in reverse order and append to bitstream
    for (matrix_i = (num_matrices - 1); matrix_i >= 0; matrix_i--){
        // place colors in bitstream based off of the angle specified
        int x_start = led_list[matrix_i].x_offset;
        int y_start = led_list[matrix_i].y_offset;
        int angle = led_list[matrix_i].angle;
        Debug("Setting matrix %d with x_start = %d, y_start = %d and angle = %d", matrix_i, x_start, y_start, angle);
        if (angle == 0){
            int x;
            for (x = x_start ; x < (x_start + DIM_OF_MATRIX); x++){
                int y;
                for (y = y_start + (DIM_OF_MATRIX - 2); y >= y_start; y -= 2){
                    bitstream[bitstream_pos++] = ((framebuffer[x][y] & 0xF) << 4) | (framebuffer[x][y+1] & 0xF);
                }
            }
        }
        if (angle == 90){  // 90 degrees counter-clockwise
            int y;
            for (y = y_start; y < (y_start + DIM_OF_MATRIX); y++){
                int x;
                for (x = x_start + 1; x < (x_start + DIM_OF_MATRIX); x += 2){
                    bitstream[bitstream_pos++] = ((framebuffer[x][y] & 0xF) << 4) | (framebuffer[x-1][y] & 0xF);
                }
            }
        }
        if (angle == 180){  // upside-down
            int x;
            for (x = (x_start + (DIM_OF_MATRIX - 1)); x >= x_start; x--){
                int y;
                for (y = y_start + 1; y < (y_start + DIM_OF_MATRIX); y += 2){
                    bitstream[bitstream_pos++] = ((framebuffer[x][y] & 0xF) << 4) | (framebuffer[x][y-1] & 0xF);
                }
            }
        }
        if (angle == 270){
            int y;
            for (y = (y_start + (DIM_OF_MATRIX - 1)); y >= y_start; y--){
                int x;
                for (x = (x_start + (DIM_OF_MATRIX - 2)); x >= x_start; x -= 2){
                    bitstream[bitstream_pos++] = ((framebuffer[x][y] & 0xF) << 4) | (framebuffer[x+1][y] & 0xF);
                }
            }
        }
    }
    return 0;
}

// closes SPI port and frees all allocated memory
int close_and_free(void){
    Debug("Closing and freeing.")
    int i;
    if (framebuffer){
        for (i = 0; i < container_width; i++){
            free(framebuffer[i]);
        }
    }
    free(framebuffer);
    if (led_list){
        free(led_list);
    }
    if (bitstream){
        free(bitstream);
    }
    close(spi);
    return 0;
}

void print_framebuffer(void){
    system("clear");  // clear terminal
    int y;
    for (y = 0; y < container_height; y++){
        int x;
        for (x = 0; x < container_width; x++){
            int pixel = framebuffer[x][y];
            if (pixel < 16)
                printf("%x ", pixel);
            else
                printf("- ");
        }
        printf("\n");
    }
}


// Python Wrappers =================================================

static PyObject *py_init_matrices(PyObject *self, PyObject *args){
    PyObject *mat_list;  // the list object
    // grab mat_list and global variables
    if (!PyArg_ParseTuple(args, "O!iii", &PyList_Type, &mat_list, &num_matrices,
        &container_width, &container_height)){
        PyErr_SetString(PyExc_TypeError, "Invalid arguments.");
        return NULL;
    }
    Debug("container_width = %d, container_height = %d, num_matrices = %d", 
        container_width, container_height, num_matrices);
    int listSize = PyList_Size(mat_list);
    if (!PyList_Check(mat_list) || listSize < 0){
        PyErr_SetString(PyExc_TypeError, "Not a list");
        return NULL;
    }
    // get led_list ready
    led_list = (struct Matrix *) malloc((listSize)*sizeof(struct Matrix));
    if (led_list == 0){
        PyErr_NoMemory();
        return NULL;
    }
    memset(led_list, '\0', (listSize)*sizeof(struct Matrix));
    // iterate through list object and place items in led_list
    int i;
    for (i = 0; i < listSize; i++){
        int x_offset, y_offset;
        int angle = 0;  // set angle to be 0 by default if not changed in tuple
        if (!PyArg_ParseTuple(PyList_GetItem(mat_list, i), "ii|i", &x_offset, &y_offset, &angle)){
            PyErr_SetString(PyExc_TypeError, "Tuple not correct.");
            return NULL;
        }
        led_list[i].x_offset = x_offset;
        led_list[i].y_offset = y_offset;
        led_list[i].angle = angle;
        Debug("Set matrix %d with x_offset = %d, y_offset = %d and angle = %d", 
            i, led_list[i].x_offset, led_list[i].y_offset, led_list[i].angle);
    }
    // initialize the framebuffer and bitstream
    return Py_BuildValue("i", init_framebuffer_and_bitstream());
}

static PyObject *py_fill(PyObject *self, PyObject *args){
    unsigned int color;
    if(!PyArg_ParseTuple(args, "I", &color)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned int!");
        return NULL;
    }
    int ret = fill(color);
    if(ret < 0){
        char error_message[50];
        sprintf(error_message, "fill(%d) returned %d", color, ret);
        PyErr_SetString(PyExc_RuntimeError, error_message);
    }
    return Py_BuildValue("i", ret);
}

static PyObject *py_line(PyObject *self, PyObject *args){
    int x1, y1, x2, y2;
    unsigned int color;
	if(!PyArg_ParseTuple(args, "iiiiI", &x1, &y1, &x2, &y2, &color)){
		PyErr_SetString(PyExc_TypeError, "Not ints!");
		return NULL;
	}
	int ret = line(x1, y1, x2, y2, color);
	if(ret < 0){
	    char error_message[50];
	    sprintf(error_message, "line(%d, %d, %d, %d, %d) returned %d", x1, y1, x2, y2, color, ret);
	    PyErr_SetString(PyExc_RuntimeError, error_message);
	}
	return Py_BuildValue("i", ret);
}

static PyObject *py_point(PyObject *self, PyObject *args){
    int x, y;
    unsigned int color = 17;
	if(!PyArg_ParseTuple(args, "iiI", &x, &y, &color)){
		PyErr_SetString(PyExc_TypeError, "Not ints!");
		return NULL;
	}
	int ret = point(x, y, color);
	if(ret < 0){
	    char error_message[50];
	    sprintf(error_message, "point(%d, %d, %d) returned %d", x, y, color, ret);
	    PyErr_SetString(PyExc_RuntimeError, error_message);
	}
	return Py_BuildValue("i", ret);
}


static PyObject *py_init_SPI(PyObject *self, PyObject *args){
	unsigned int speed;
	int mode;
	if(!PyArg_ParseTuple(args, "Ii", &speed, &mode)){
		PyErr_SetString(PyExc_TypeError, "Not an unsigned int and int!");
		return NULL;
	}
	return Py_BuildValue("i", start_SPI(speed, mode));
}

static PyObject *py_flush(PyObject *self, PyObject *args){
    // show on terminal if flag enabled
    if (display_on_terminal){
        print_framebuffer();
    }
    update_bitstream();
    return Py_BuildValue("i", write_bytes(spi, bitstream, bitstream_SIZE));
}

static PyObject *py_shutdown_matrices(PyObject *self, PyObject *args){
	return Py_BuildValue("i", close_and_free());
}

static PyMethodDef led_driver_methods[] = {
	{"init_SPI", py_init_SPI, METH_VARARGS, "Initialize the SPI with given speed and port."},
    {"init_matrices", py_init_matrices, METH_VARARGS, "Initializes the give LED matrices in the list."},
    {"flush", py_flush, METH_NOARGS, "Converts current frame buffer to a bistream and then sends it to SPI port."},
	{"shutdown_matrices", py_shutdown_matrices, METH_NOARGS, "Closes the SPI and frees all memory."},
	{"point", py_point, METH_VARARGS, "Sets a point in the frame buffer."},
	{"line", py_line, METH_VARARGS, "Sets a line from given source to destination."},
    {"fill", py_fill, METH_VARARGS, "Fills all matrices with the given color."},
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
