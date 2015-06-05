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
#include <math.h>
#include <stdio.h>
#include <malloc.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <alsa/asoundlib.h>

#define DEFAULT_FORMAT		SND_PCM_FORMAT_S16_LE
#define DEFAULT_RATE 		44100
#define DEFAULT_CHANNELS 	1

#define MAX_SAMPLES 4096

static snd_pcm_t *handle;
static snd_pcm_uframes_t chunk_size = 0;
static size_t bits_per_sample, bits_per_frame;
static size_t chunk_bytes;
static int audio_mix_buf[MAX_SAMPLES];
static short audio_buf[MAX_SAMPLES];


int audio_init(void)
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
	err = err || snd_pcm_hw_params_set_rate(handle, params, DEFAULT_RATE, 0);
	err = err || snd_pcm_hw_params_set_buffer_size(handle, params, 4096);
	err = err || snd_pcm_hw_params(handle, params);
	if (err < 0) return -EIO;

	snd_pcm_hw_params_get_period_size(params, &chunk_size, 0);
	bits_per_sample = snd_pcm_format_physical_width(DEFAULT_FORMAT);
	bits_per_frame = bits_per_sample * DEFAULT_CHANNELS;
	chunk_bytes = chunk_size * bits_per_frame / 8;

	return 0;
}

int audio_shutdown(void)
{
	snd_pcm_close(handle);
	snd_config_update_free_global();

	return 0;
}

static ssize_t pcm_write(char *data, size_t count)
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

static void play(void *audio_bytes, int len)
{
	int ret;

    ret = pcm_write(audio_bytes, 512);
    if (ret < 0) {
		ret = snd_pcm_recover(handle, ret, 0);
    }
    if (ret < 0) return;
}

static void flush(void)
{
	snd_pcm_nonblock(handle, 0);
	snd_pcm_drain(handle);
	snd_pcm_prepare(handle);
	snd_pcm_start(handle);
}

static void stop(void)
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

static PyObject *py_play(PyObject *self, PyObject *args){
    short *s;
    int i, j;
    PyObject* arg1;
    PyObject* arg2;
    PyObject* chunks;
    PyObject* chunk;
    PyObject* gains;
    PyObject* gain;
    int len, gains_len;
    double g;

    if (!PyArg_ParseTuple(args, "OO", &arg1, &arg2)) {
        PyErr_SetString(PyExc_TypeError, "Expected two args");
        return NULL;
    }

    chunks = PySequence_Fast(arg1, "Expected a sequence");
    len = PySequence_Size(arg1);
    gains = PySequence_Fast(arg2, "Expected a sequence");
    gains_len = PySequence_Size(arg2);
    if (len != gains_len) {
        Py_DECREF(gains);
        Py_DECREF(chunks);
        PyErr_SetString(PyExc_TypeError, "Chunks and gains must have equal lengths");
        return NULL;
    }
    memset(audio_mix_buf, 0, chunk_size * sizeof(int));
    for (i = 0; i < len; i++) {
        chunk = PySequence_Fast_GET_ITEM(chunks, i);
        s = (short *) PyBytes_AsString(chunk);
        gain = PySequence_Fast_GET_ITEM(gains, i);
        g = PyFloat_AsDouble(gain);
        for (j = 0; j < chunk_size; j++) {
            audio_mix_buf[j] += (s[j] * g);
        }
    }
    for (j = 0; j < chunk_size; j++) {
        register unsigned int high_short = ((unsigned int) audio_mix_buf[j]) >> 15;
        if (high_short == 0x0001FFFF || high_short == 0x00000000) {
            audio_buf[j] = audio_mix_buf[j];
        } else if (high_short & 0x10000) {
            audio_buf[j] = 0x8000;
        } else {
            audio_buf[j] = 0x7FFF;
        }
    }
    play(audio_buf, 0);
    Py_DECREF(gains);
    Py_DECREF(chunks);

    return Py_BuildValue("");
}

static PyObject *py_note(PyObject *self, PyObject *args){
    short note[512];
    int offset;
    float freq;
    int i;
    if (!PyArg_ParseTuple(args, "if", &offset, &freq)) {
        PyErr_SetString(PyExc_TypeError, "Expected (int chunk, float freq)");
        return NULL;
    }

    offset *= chunk_size;
    for (i = 0; i < chunk_size; i++) {
        note[i] = 32767*sin(((offset+i)*2*3.14*freq)/DEFAULT_RATE);
    }
    
    return Py_BuildValue("y#", note, chunk_size*2);
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
    {"play", py_play, METH_VARARGS, "Play audio buffers to default output"},
    {"note", py_note, METH_VARARGS, "Create sinewave buffer"},
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
