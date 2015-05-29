/*
 * mixer.c
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

#define MAX_MATRICES 50

#define _GNU_SOURCE
#include <stdio.h>
#include <malloc.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <alsa/asoundlib.h>

#define DEFAULT_FORMAT		SND_PCM_FORMAT_S16_LE
#define DEFAULT_SPEED 		44100
#define DEFAULT_CHANNELS 	1

static snd_pcm_t *handle;
static u_char *audiobuf = NULL;
static snd_pcm_uframes_t chunk_size = 0;
static size_t bits_per_sample, bits_per_frame;
static size_t chunk_bytes;
static int fd = -1;

static void playback(char *filename);

int go()
{
	char *pcm_name = "default";
	int err, c;
	snd_pcm_hw_params_t *params;

	err = snd_pcm_open(&handle, pcm_name, SND_PCM_STREAM_PLAYBACK, 0);
	if (err < 0) {
		printf("audio open error: %s", snd_strerror(err));
		return 1;
	}

	audiobuf = (u_char *)malloc(1024);
	if (audiobuf == NULL) {
		printf("not enough memory");
		return 1;
	}

	snd_pcm_hw_params_alloca(&params);

	err = snd_pcm_hw_params_any(handle, params);
    err = err || snd_pcm_hw_params_set_access(handle, params, SND_PCM_ACCESS_RW_INTERLEAVED);
	err = err || snd_pcm_hw_params_set_format(handle, params, DEFAULT_FORMAT);
	err = err || snd_pcm_hw_params_set_channels(handle, params, DEFAULT_CHANNELS);
	err = err || snd_pcm_hw_params_set_rate(handle, params, DEFAULT_SPEED, 0);
	err = err || snd_pcm_hw_params(handle, params);
	if (err < 0) {
		printf("snd_pcm_hw_params_*() failure");
		exit(1);
	}

	snd_pcm_hw_params_get_period_size(params, &chunk_size, 0);
	bits_per_sample = snd_pcm_format_physical_width(DEFAULT_FORMAT);
	bits_per_frame = bits_per_sample * DEFAULT_CHANNELS;
	chunk_bytes = chunk_size * bits_per_frame / 8;
	audiobuf = realloc(audiobuf, chunk_bytes);
	if (audiobuf == NULL) {
		printf("not enough memory");
		exit(1);
	}

    playback("/home/pi/python_games/match1.wav");

	snd_pcm_close(handle);
	free(audiobuf);
	snd_config_update_free_global();

	return EXIT_SUCCESS;
}

static ssize_t safe_read(int fd, void *buf, size_t count)
{
	ssize_t result = 0, res;

	while (count > 0) {
		if ((res = read(fd, buf, count)) == 0)
			break;
		if (res < 0)
			return result > 0 ? result : res;
		count -= res;
		result += res;
		buf = (char *)buf + res;
	}
	return result;
}


static ssize_t pcm_write(u_char *data, size_t count)
{
	ssize_t r;
	ssize_t result = 0;

	if (count < chunk_size) {
		return 0;
	}
	while (count > 0) {
		r = snd_pcm_writei(handle, data, count);
		if (r > 0) {
			result += r;
			count -= r;
			data += r * bits_per_frame / 8;
		} else {
            return r;
        }
	}
	return result;
}

static void playback(char *name)
{
	int ret;
	int bytes_read, bytes_written;

    if ((fd = open64(name, O_RDONLY, 0)) == -1) {
        perror(name);
        exit(1);
	}

    bytes_written = bytes_read = 0;
	while (bytes_written == bytes_read) {
        ret = safe_read(fd, audiobuf, chunk_bytes);
        if (ret < 0) exit(1);

		bytes_read = ret * 8 / bits_per_frame;
		bytes_written = pcm_write(audiobuf, bytes_read);
        if (bytes_written < 0) exit(1);
	}
	snd_pcm_nonblock(handle, 0);
	snd_pcm_drain(handle);
	if (fd != 0)
		close(fd);
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
    if (ret < 0) {
        PyErr_SetString(PyExc_IOError, "Failed to init SPI port.");
        return NULL;
    }
    return Py_BuildValue("");
}   

static PyObject *py_send(PyObject *self, PyObject *args){
    char *s;
    int len;
    printf("dude\n");
    go();
    if(!PyArg_ParseTuple(args, "y#", &s, &len)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned int!");
        return NULL;
    }
    printf("%c%c%c\n", s[0], s[1], s[2]);
    return Py_BuildValue("y#", s, len);
}

static PyMethodDef mixer_methods[] = {
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

static int mixer_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int mixer_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}


static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "mixer",
        NULL,
        sizeof(struct module_state),
        mixer_methods,
        NULL,
        mixer_traverse,
        mixer_clear,
        NULL
};

#define INITERROR return NULL

PyObject *
PyInit_mixer(void)

#else
#define INITERROR return

void initmixer(void)
#endif
{
    struct module_state *st;

#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("mixer", mixer_methods);
#endif

    if (module == NULL)
        INITERROR;

    st = GETSTATE(module);

    st->error = PyErr_NewException("mixer.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
