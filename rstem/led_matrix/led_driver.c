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

#define COORDS_TO_INDEX(x, y) ((x)*container_height + (y))

#define SIGN(x) (((x) >= 0) ? 1 : -1)

int debug = 0;
#define Debug(args...) if (debug) {printf("LED_DRIVER: " args); printf("\n");}



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
unsigned int *framebuffer;   // information on all pixels (physical or not)
int framebuffer_size;
PyObject *numpy_array = NULL;  // if null we are using original framebuffer
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
//		.delay_usecs = 100,
	};
	int ret = ioctl(dev, SPI_IOC_MESSAGE(1), &tr);
	return ret;
}

// memory commands ===========================================

void free_framebuffer(void){
    if (numpy_array) {
        Py_DECREF(numpy_array);
        numpy_array = NULL;
    } else {
        free(framebuffer);
    }
}

// closes SPI port and frees all allocated memory
int close_and_free(void){
    Debug("Closing and freeing.")
    if (framebuffer) {
        free_framebuffer();
    }
    framebuffer = NULL;
    if (led_list){
        free(led_list);
    }
    led_list = NULL;
    if (bitstream){
        free(bitstream);
    }
    bitstream = NULL;
    close(spi);
    return 0;
}

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
	Debug("num_of_matrices = %d", count-1)
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

int point(int x, int y, unsigned int color) {
    Debug("Setting point at (%d,%d) with color %d", x, y, color);
    if (x >= container_width || x < 0 || y >= container_height || y < 0)
        return -1;
    framebuffer[COORDS_TO_INDEX(x,y)] = color;
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
    Debug("framebuffer_size = %d*%d*%d", container_height, container_width, sizeof(unsigned int));
    framebuffer_size = container_height*container_width*sizeof(unsigned int);
    
    Debug("Initializing framebuffer with size %d", framebuffer_size);
    framebuffer = (unsigned int *) malloc(framebuffer_size);
    memset(framebuffer, 0, framebuffer_size);
    if (framebuffer == 0){
        Debug("Error mallocing framebuffer");
        goto freeLEDList;
    }
    Debug("Initializing bitstream with size %d", num_matrices*NUM_BYTES_MATRIX);
    bitstream = (unsigned char *) malloc(num_matrices*NUM_BYTES_MATRIX);
    if (bitstream == 0){
        Debug("Error mallocing bitstream");
        goto freeframebuffer;
    }
    memset(bitstream, '\0', num_matrices*NUM_BYTES_MATRIX);
    return 0;

    // Clean up on malloc error
    freeframebuffer:
        free_framebuffer();
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
                    bitstream[bitstream_pos++] = ((framebuffer[COORDS_TO_INDEX(x,y)] & 0xF) << 4) | (framebuffer[COORDS_TO_INDEX(x,y+1)] & 0xF);
                }
            }
        }
        if (angle == 90){  // 90 degrees counter-clockwise
            int y;
            for (y = y_start; y < (y_start + DIM_OF_MATRIX); y++){
                int x;
                for (x = x_start + 1; x < (x_start + DIM_OF_MATRIX); x += 2){
                    bitstream[bitstream_pos++] = ((framebuffer[COORDS_TO_INDEX(x,y)] & 0xF) << 4) | (framebuffer[COORDS_TO_INDEX(x-1,y)] & 0xF);
                }
            }
        }
        if (angle == 180){  // upside-down
            int x;
            for (x = (x_start + (DIM_OF_MATRIX - 1)); x >= x_start; x--){
                int y;
                for (y = y_start + 1; y < (y_start + DIM_OF_MATRIX); y += 2){
                    bitstream[bitstream_pos++] = ((framebuffer[COORDS_TO_INDEX(x,y)] & 0xF) << 4) | (framebuffer[COORDS_TO_INDEX(x,y-1)] & 0xF);
                }
            }
        }
        if (angle == 270){
            int y;
            for (y = (y_start + (DIM_OF_MATRIX - 1)); y >= y_start; y--){
                int x;
                for (x = (x_start + (DIM_OF_MATRIX - 2)); x >= x_start; x -= 2){
                    bitstream[bitstream_pos++] = ((framebuffer[COORDS_TO_INDEX(x,y)] & 0xF) << 4) | (framebuffer[COORDS_TO_INDEX(x+1,y)] & 0xF);
                }
            }
        }
    }
    return 0;
}



void print_framebuffer(void){
    int y;
    // Send terminal the ANSI clear screen escape sequence.
    printf("%c[H%c[2J", 0x1B, 0x1B);
    for (y = 0; y < container_height; y++){
        int x;
        for (x = 0; x < container_width; x++){
            int pixel = framebuffer[COORDS_TO_INDEX(x,y)];
            if (pixel == 0) {
                printf(". ");
            } else if (pixel < 16) {
                printf("%X ", pixel);
            } else {
                printf("- ");
            }
        }
        printf("\n");
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
    Debug("container_width = %d, container_height = %d, num_matrices = %d", 
        container_width, container_height, num_matrices);
/*    int num_matrices = PyList_Size(mat_list);*/
/*    if (!PyList_Check(mat_list) || num_matrices < 0){*/
/*        PyErr_SetString(PyExc_TypeError, "Not a list");*/
/*        return NULL;*/
/*    }*/
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
        Debug("Set matrix %d with x_offset = %d, y_offset = %d and angle = %d", 
            i, led_list[i].x_offset, led_list[i].y_offset, led_list[i].angle);
    }
    // initialize the framebuffer and bitstream
    int ret = init_framebuffer_and_bitstream();
    if (ret < 0){
        char error_message[50];
        sprintf(error_message, "init_matrices returned %d", ret);
        PyErr_SetString(PyExc_RuntimeError, error_message);
    }
    return Py_BuildValue("i", ret);
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
	import_array();
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

static PyObject *py_display_on_terminal(PyObject *self, PyObject *args){
    if (display_on_terminal)
        display_on_terminal = 0;
    else
        display_on_terminal = 1;
	return Py_BuildValue("i", 1);
}

static PyObject *py_frame(PyObject *self, PyObject *args){
    PyObject *input_array = NULL;
    if (!PyArg_ParseTuple(args, "O!", &PyArray_Type, &input_array)){
        Debug("Not an array.");
		PyErr_SetString(PyExc_TypeError, "Not an array!");
		return NULL;
	}
	Debug("Passed args parsing, now freeing old framebuffer.");
	free_framebuffer();
	framebuffer = NULL;
	
	Debug("Attempt to get numpy array object.");
	numpy_array = PyArray_FROM_OTF(input_array, NPY_INT, NPY_INOUT_ARRAY);
	if (numpy_array == NULL) {
	    Py_XDECREF(numpy_array);
	    numpy_array = NULL;
	    PyErr_SetString(PyExc_RuntimeError, "Could not get numpy array!");
	    return NULL;
    }
	
	// checking stuff
	if (PyArray_NDIM(numpy_array) != 2){
	    PyErr_SetString(PyExc_ValueError, "Numpy array must be 2D!");
	    return NULL;
	}
	if (PyArray_DIM(numpy_array, 0) != container_width
	    || PyArray_DIM(numpy_array, 1) != container_height){
	    PyErr_SetString(PyExc_ValueError, "Numpy array dimensions must be the same as container!");
	    return NULL;   
	}
	
	Debug("Attempt to cast a framebuffer.");
	framebuffer = (unsigned int *) PyArray_DATA(numpy_array);

	Debug("Current framebuffer pointer %p", framebuffer);
	print_framebuffer();
	return Py_BuildValue("i", 1);
}

static PyMethodDef led_driver_methods[] = {
	{"init_SPI", py_init_SPI, METH_VARARGS, "Initialize the SPI with given speed and port."},
	{"init_matrices", py_init_matrices, METH_VARARGS, "Initializes the give LED matrices in the list."},
	{"flush", py_flush, METH_NOARGS, "Converts current frame buffer to a bistream and then sends it to SPI port."},
	{"shutdown_matrices", py_shutdown_matrices, METH_NOARGS, "Closes the SPI and frees all memory."},
	{"point", py_point, METH_VARARGS, "Sets a point in the frame buffer."},
	{"line", py_line, METH_VARARGS, "Sets a line from given source to destination."},
    {"frame", py_frame, METH_VARARGS, "Exchanges current framebuffer for a numpy framebuffer."},
	{"fill", py_fill, METH_VARARGS, "Fills all matrices with the given color."},
	{"detect", py_num_of_matrices, METH_NOARGS, "Returns the number of matrices connected"},
	{"display_on_terminal", py_display_on_terminal, METH_NOARGS, "Toggles on and off display_on_terminal mode"},
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
