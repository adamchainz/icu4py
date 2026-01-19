#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <unicode/uversion.h>

namespace {

PyMethodDef version_module_methods[] = {
    {nullptr, nullptr, 0, nullptr}
};

int icu4py_version_exec(PyObject* m) {
    UVersionInfo versionArray;
    u_getVersion(versionArray);

    PyObject* version_tuple = Py_BuildValue("(iiii)",
        versionArray[0],
        versionArray[1],
        versionArray[2],
        versionArray[3]
    );
    if (PyModule_AddObject(m, "icu_version_info", version_tuple) < 0) {
        Py_DECREF(version_tuple);
        return -1;
    }

    if (PyModule_AddStringConstant(m, "icu_version", U_ICU_VERSION) < 0) {
        return -1;
    }

    return 0;
}

PyModuleDef_Slot version_slots[] = {
    {Py_mod_exec, reinterpret_cast<void*>(icu4py_version_exec)},
#ifdef Py_GIL_DISABLED
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, nullptr}
};

static PyModuleDef versionmodule = {
    PyModuleDef_HEAD_INIT,
    "icu4py._version",
    "ICU version information",
    0,
    version_module_methods,
    version_slots,
    nullptr,
    nullptr,
    nullptr,
};

}  // anonymous namespace

PyMODINIT_FUNC PyInit__version() {
    return PyModuleDef_Init(&versionmodule);
}
