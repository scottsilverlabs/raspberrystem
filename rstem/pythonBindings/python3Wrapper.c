//for xxmodule.c

struct xxstate{
  PyObject *ErrorObject;
  PyObject *Xxo_Type;
};

#define xxstate(o) ((struct xxstate*)PyModule_GetState(o))

static int xx_traverse(PyObject *m, visitproc v,
                       void *arg)
{
  Py_VISIT(xxstate(m)->ErrorObject);
  Py_VISIT(xxstate(m)->Xxo_Type);
  return 0;
}

static int xx_clear(PyObject *m)
{
  Py_CLEAR(xxstate(m)->ErrorObject);
  Py_CLEAR(xxstate(m)->Xxo_Type);
  return 0;
}

static struct PyModuleDef xxmodule = {
  {}, /* m_base */
  sizeof(struct xxstate),
  &xx_methods,
  0,  /* m_reload */
  xx_traverse,
  xx_clear,
  0,  /* m_free - not needed, since all is done in m_clear */
}

PyObject*
PyInit_xx()
{
  PyObject *res = PyModule_New("xx", &xxmodule);
  if (!res) return NULL;
  xxstate(res)->ErrorObject = PyErr_NewException("xx.error", NULL, NULL);
  if (!xxstate(res)->ErrorObject) {
    Py_DECREF(res);
    return NULL;
  }
  xxstate(res)->XxoType = PyType_Copy(&Xxo_Type);
  if (!xxstate(res)->Xxo_Type) {
    Py_DECREF(res);
    return NULL;
  }
  return res;
}
