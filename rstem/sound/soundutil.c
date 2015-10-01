/*
 * soundutil.c
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

#define DEFAULT_FORMAT		SND_PCM_FORMAT_S16_LE
#define DEFAULT_RATE 		44100
#define DEFAULT_CHANNELS 	1
#define CHUNK_SIZE 512

static PyObject *py_note(PyObject *self, PyObject *args){
    short note[512];
    int offset;
    float freq;
    int i;
    if (!PyArg_ParseTuple(args, "if", &offset, &freq)) {
        PyErr_SetString(PyExc_TypeError, "Expected (int chunk, float freq)");
        return NULL;
    }

    offset *= CHUNK_SIZE;
    for (i = 0; i < CHUNK_SIZE; i++) {
        note[i] = 32767*sin(((offset+i)*2*3.14*freq)/DEFAULT_RATE);
    }
    
    return Py_BuildValue("y#", note, CHUNK_SIZE*2);
}

static PyMethodDef soundutil_methods[] = {
    {"note", py_note, METH_VARARGS, "Create sinewave buffer"},
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

static int soundutil_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int soundutil_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}


static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "soundutil",
        NULL,
        sizeof(struct module_state),
        soundutil_methods,
        NULL,
        soundutil_traverse,
        soundutil_clear,
        NULL
};

#define INITERROR return NULL

PyObject *
PyInit_soundutil(void)

#else
#define INITERROR return

void initsoundutil(void)
#endif
{
    struct module_state *st;

#if PY_MAJOR_VERSION >= 3
    PyObject *module = PyModule_Create(&moduledef);
#else
    PyObject *module = Py_InitModule("soundutil", soundutil_methods);
#endif

    if (module == NULL)
        INITERROR;

    st = GETSTATE(module);

    st->error = PyErr_NewException("soundutil.Error", NULL, NULL);
    if (st->error == NULL) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
