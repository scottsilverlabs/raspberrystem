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
static snd_pcm_uframes_t chunk_size = 0;
static size_t bits_per_sample, bits_per_frame;
static size_t chunk_bytes;

int audio_init()
{
	char *pcm_name = "default";
	int err;
	snd_pcm_hw_params_t *params;

	err = snd_pcm_open(&handle, pcm_name, SND_PCM_STREAM_PLAYBACK, 0);
	if (err < 0) return -ENODEV;

	snd_pcm_hw_params_alloca(&params);

	err = snd_pcm_hw_params_any(handle, params);
    err = err || snd_pcm_hw_params_set_access(handle, params, SND_PCM_ACCESS_RW_INTERLEAVED);
	err = err || snd_pcm_hw_params_set_format(handle, params, DEFAULT_FORMAT);
	err = err || snd_pcm_hw_params_set_channels(handle, params, DEFAULT_CHANNELS);
	err = err || snd_pcm_hw_params_set_rate(handle, params, DEFAULT_SPEED, 0);
	err = err || snd_pcm_hw_params_set_buffer_size(handle, params, 4096);
	err = err || snd_pcm_hw_params(handle, params);
	if (err < 0) return -EIO;

	snd_pcm_hw_params_get_buffer_time(params, &chunk_size, 0);
    printf("buf: %d\n", chunk_size);
	snd_pcm_hw_params_get_buffer_size(params, &chunk_size);
    printf("buf: %d\n", chunk_size);
	snd_pcm_hw_params_get_period_size(params, &chunk_size, 0);
	bits_per_sample = snd_pcm_format_physical_width(DEFAULT_FORMAT);
	bits_per_frame = bits_per_sample * DEFAULT_CHANNELS;
	chunk_bytes = chunk_size * bits_per_frame / 8;

	return 0;
}

int audio_shutdown()
{
	snd_pcm_close(handle);
	snd_config_update_free_global();

	return 0;
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

static void play(const char *audio_bytes, int len)
{
	int ret;

    ret = pcm_write(audio_bytes, 512);
    if (ret < 0) return;

	//snd_pcm_nonblock(handle, 0);
	//snd_pcm_drain(handle);
}

static void flush()
{
	snd_pcm_nonblock(handle, 0);
	snd_pcm_drain(handle);
	snd_pcm_prepare(handle);
	snd_pcm_start(handle);
}

static void stop()
{
	snd_pcm_nonblock(handle, 0);
	snd_pcm_drop(handle);
	snd_pcm_prepare(handle);
	snd_pcm_start(handle);
}

// Python Wrappers =================================================


static PyObject *py_init(PyObject *self, PyObject *args){
    audio_init();
    return Py_BuildValue("");
}   

static PyObject *py_shutdown(PyObject *self, PyObject *args){
    audio_shutdown();
    return Py_BuildValue("");
}   

static PyObject *py_mix(PyObject *self, PyObject *args){
    char *s;
    int len;
    audio_init();
    if(!PyArg_ParseTuple(args, "y#", &s, &len)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned int!");
        return NULL;
    }
    printf("%c%c%c\n", s[0], s[1], s[2]);
    return Py_BuildValue("y#", s, len);
}

static PyObject *py_play(PyObject *self, PyObject *args){
    char *s;
    int len;
    if(!PyArg_ParseTuple(args, "y#", &s, &len)){
        PyErr_SetString(PyExc_TypeError, "Not an unsigned int!");
        return NULL;
    }
    play(s, len);

    return Py_BuildValue("y#", s, len);
}

static PyObject *py_flush(PyObject *self, PyObject *args){
    flush();
    return Py_BuildValue("");
}

static PyObject *py_stop(PyObject *self, PyObject *args){
    stop();
    return Py_BuildValue("");
}

static PyMethodDef mixer_methods[] = {
    {"init", py_init, METH_VARARGS, "Initialize audio"},
    {"shutdown", py_shutdown, METH_VARARGS, "Shutdown audio"},
    {"mix", py_mix, METH_VARARGS, "Mix multiple channels with individual gains"},
    {"play", py_play, METH_VARARGS, "Play audio buffer to default output"},
    {"flush", py_flush, METH_VARARGS, "Flush audio data"},
    {"stop", py_stop, METH_VARARGS, "Stop audio data"},
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
