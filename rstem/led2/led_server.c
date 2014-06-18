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
// number of bits in a matrix
#define NUM_BITS_MATRIX (DIM_OF_MATRIX*DIM_OF_MATRIX*SIZE_OF_PIXEL)

#define PIXEL_WIDTH (DIM_OF_MATRIX*led.num_cols)
#define PIXEL_HEIGHT (DIM_OF_MATRIX*led.num_rows)

#define MAT_ROW(x,y) ((y)/DIM_OF_MATRIX)
#define MAT_COL(x,y) ((x)/DIM_OF_MATRIX)
#define NUM_MATRICES (led.num_cols*led.num_rows)
// index of matrix with order relative to the frameBuffer bitstream
#define MAT_INDEX(x,y) ((NUM_MATRICES - 1) - (MAT_ROW(x,y)*led.num_cols + MAT_COL(x,y)))

// tells you if (x,y) is in matrix (USING STD ANGLE only!)
#define IN_MATRIX(x,y) ((x) >= 0 && (x) < PIXEL_WIDTH && (y) >= 0 && (y) < PIXEL_HEIGHT)

#define FRAME_BUFFER_SIZE (NUM_BYTES_MATRIX*NUM_MATRICES)

int spi;
unsigned char spiMode;
unsigned char bitsPerTrans;
unsigned int spiSpeed;

int main(){
    // testing purpose TODO remove
}

struct LEDMatrix {
    unsigned char *frameBuffer;
    int num_cols;
    int num_rows;
    int zigzag;
    int angle;
};

struct LEDMatrix led;


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

int fill(unsigned int color){
    if (color > 0xF){
        return -1;
    }
    color = ((color & 0xF) << 4) | (color & 0xF);
    int i;
    // TODO memsetle
    for (i = 0; i < FRAME_BUFFER_SIZE; i++){
        led.frameBuffer[i] = (unsigned char) color;
    }
    return 0;
}

void convert_to_std_angle(int *x, int *y){
    if (led.angle == 90){
        int oldx = *x;
        *x = *y;
        *y = (PIXEL_HEIGHT - 1) - oldx;
    } else if (led.angle == 180){
        *x = (PIXEL_WIDTH - 1) - *x;
        *y = (PIXEL_HEIGHT - 1) - *y;
    } else if (led.angle == 270){
        int oldy = *y;
        *y = *x;
        *x = (PIXEL_WIDTH - 1) - oldy;
    }
}


int point_to_bitPos(int x, int y){

    int mat_row = MAT_ROW(x,y);
    // subtract off above matrix row and column so we can tread y relative to matrix row
    y = (y - mat_row*DIM_OF_MATRIX);
    // if on odd matrix row and zigzag enabled, we need to flip x and y coords
    // (this allows us to treat x,y,mat_row,and mat_col as if zigzag == False)
    if (mat_row % 2 == 1 && led.zigzag){
        x = (DIM_OF_MATRIX*led.num_cols - 1) - x;
        y = (DIM_OF_MATRIX - 1) - y;
    }
    // subtract off left matrix columns so we can treat x relative to matrix element
    x = (x - MAT_COL(x,y)*DIM_OF_MATRIX);


    // x and y now relative to matrix element
    // get bitPos relative to matrix element
    int bitPosCol = x*DIM_OF_MATRIX*SIZE_OF_PIXEL;
    int bitPosColOffset = (DIM_OF_MATRIX - 1 - y)*SIZE_OF_PIXEL;
    int bitPos = bitPosCol + bitPosColOffset;

    // update bitPos to be absolute index of entire matrix
    bitPos += MAT_INDEX(x,y)*NUM_BITS_MATRIX;

    return bitPos;
}

int point(int x, int y, unsigned int color) {
    convert_to_std_angle(&x,&y);
    if (!IN_MATRIX(x,y)){
        return 0;
    }
    if (color > 0xF){
        return -1;
    }
    int bitPos = point_to_bitPos(x,y);
    int bytePos = bitPos/8;
    // swap nibble (low to height, hight to low)
    if (bitPos % 8 == 0){
        // put nibble on low side
        led.frameBuffer[bytePos] = (led.frameBuffer[bytePos] & 0xF0) | (color & 0xF);
    } else {
        // put nibble on high side
        led.frameBuffer[bytePos] = ((color & 0xF) << 4) | (led.frameBuffer[bytePos] & 0xF);
    }
    return 0;
}

int line(int x1, int y1, int x2, int y2, unsigned int color){
    return 0;
}

int initLED(int num_rows, int num_cols, int zigzag, int angle){
    led.frameBuffer = (unsigned char *) malloc(num_cols*num_rows*NUM_BYTES_MATRIX);
    led.num_rows = num_rows;
    led.num_cols = num_cols;
    led.zigzag = zigzag;
    led.angle = angle;
    return 0;
}

static PyObject *PyInitLED(PyObject *self, PyObject *args){
    int num_rows, num_cols, zigzag, angle;
	if(!PyArg_ParseTuple(args, "iiii", &num_rows, &num_cols, &zigzag, &angle)){
		PyErr_SetString(PyExc_TypeError, "Not ints!");
		return NULL;
	}
	if(initLED(num_rows, num_cols, zigzag, angle) < 0){
	    PyErr_SetString(PyExc_RuntimeError, "Something bad happned...");
	}
	return Py_BuildValue("i", 1);
}

static PyObject *PyFill(PyObject *self, PyObject *args){
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

static PyObject *PyLine(PyObject *self, PyObject *args){
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

static PyObject *PyPoint(PyObject *self, PyObject *args){
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


static PyObject *initSPI(PyObject *self, PyObject *args){
	unsigned int speed;
	int mode;
	if(!PyArg_ParseTuple(args, "Ii", &speed, &mode)){
		PyErr_SetString(PyExc_TypeError, "Not an unsigned int and int!");
		return NULL;
	}
	return Py_BuildValue("i",startSPI(speed, mode));
}

static PyObject *PyFlush(PyObject *self, PyObject *args){
    return Py_BuildValue("i", writeBytes(spi, led.frameBuffer, FRAME_BUFFER_SIZE));
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
    {"flush2", PyFlush, METH_NOARGS},
	{"initSPI", initSPI, METH_VARARGS},
	{"closeSPI", closeSPI, METH_NOARGS},
	{"point", PyPoint, METH_VARARGS},
	{"line", PyLine, METH_VARARGS},
	{"initLED", PyInitLED, METH_VARARGS},
    {"fill", PyFill, METH_VARARGS},
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
