#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <string>
#include <unicode/locid.h>
#include <unicode/strenum.h>
#include "locale_types.h"

namespace {

using icu::Locale;
using icu4py::LocaleObject;

void Locale_dealloc(LocaleObject* self) {
    delete self->locale;
    Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyObject* Locale_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    auto* self = reinterpret_cast<LocaleObject*>(type->tp_alloc(type, 0));
    if (self != nullptr) {
        self->locale = nullptr;
    }
    return reinterpret_cast<PyObject*>(self);
}

int Locale_init(LocaleObject* self, PyObject* args, PyObject* kwds) {
    const char* language = nullptr;
    const char* country = nullptr;
    const char* variant = nullptr;
    PyObject* extensions = nullptr;

    static const char* kwlist[] = {"language", "country", "variant", "extensions", nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|zzO",
                                     const_cast<char**>(kwlist),
                                     &language, &country, &variant, &extensions)) {
        return -1;
    }

    const char* keywords_and_values = nullptr;
    std::string keywords_str;

    if (extensions != nullptr && extensions != Py_None) {
        if (!PyDict_Check(extensions)) {
            PyErr_SetString(PyExc_TypeError, "extensions must be a dict or None");
            return -1;
        }

        Py_ssize_t pos = 0;
        PyObject* key;
        PyObject* value;
        bool first = true;
        bool err = false;

#ifdef Py_GIL_DISABLED
        Py_BEGIN_CRITICAL_SECTION(extensions);
#endif

        while (PyDict_Next(extensions, &pos, &key, &value)) {
            if (!PyUnicode_Check(key)) {
                PyErr_SetString(PyExc_TypeError, "extension keys must be strings");
                err = true;
                break;
            }
            if (!PyUnicode_Check(value)) {
                PyErr_SetString(PyExc_TypeError, "extension values must be strings");
                err = true;
                break;
            }

            const char* key_str = PyUnicode_AsUTF8(key);
            if (key_str == nullptr) {
              err = true;
              break;
            }
            const char* value_str = PyUnicode_AsUTF8(value);
            if (value_str == nullptr) {
              err = true;
              break;
            }

            if (!first) {
                keywords_str += ";";
            }
            keywords_str += key_str;
            keywords_str += "=";
            keywords_str += value_str;
            first = false;
        }
#ifdef Py_GIL_DISABLED
        Py_END_CRITICAL_SECTION();
#endif
        if (err) {
            return -1;
        }

        if (!keywords_str.empty()) {
            keywords_and_values = keywords_str.c_str();
        }
    }

    self->locale = new Locale(language, country, variant, keywords_and_values);

    return 0;
}

PyObject* Locale_get_bogus(LocaleObject* self, void* closure) {
    if (self->locale->isBogus()) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

PyObject* Locale_get_language(LocaleObject* self, void* closure) {
    const char* language = self->locale->getLanguage();
    return PyUnicode_FromString(language);
}

PyObject* Locale_get_country(LocaleObject* self, void* closure) {
    const char* country = self->locale->getCountry();
    return PyUnicode_FromString(country);
}

PyObject* Locale_get_variant(LocaleObject* self, void* closure) {
    const char* variant = self->locale->getVariant();
    return PyUnicode_FromString(variant);
}

PyObject* Locale_get_extensions(LocaleObject* self, void* closure) {
    UErrorCode status = U_ZERO_ERROR;
    icu::StringEnumeration* keywords = self->locale->createKeywords(status);

    if (U_FAILURE(status) || keywords == nullptr) {
        return PyDict_New();
    }

    PyObject* dict = PyDict_New();
    if (dict == nullptr) {
        delete keywords;
        return nullptr;
    }

    const char* keyword;
    while ((keyword = keywords->next(nullptr, status)) != nullptr) {
        if (U_FAILURE(status)) {
            break;
        }

        std::string value_str;
        const int32_t capacity = 256;
        char buffer[capacity];

        int32_t length = self->locale->getKeywordValue(keyword, buffer, capacity, status);
        if (U_FAILURE(status)) {
            break;
        }

        value_str.assign(buffer, length);

        PyObject* key_obj = PyUnicode_FromString(keyword);
        PyObject* value_obj = PyUnicode_FromString(value_str.c_str());

        if (key_obj == nullptr || value_obj == nullptr) {
            Py_XDECREF(key_obj);
            Py_XDECREF(value_obj);
            Py_DECREF(dict);
            delete keywords;
            return nullptr;
        }

        if (PyDict_SetItem(dict, key_obj, value_obj) < 0) {
            Py_DECREF(key_obj);
            Py_DECREF(value_obj);
            Py_DECREF(dict);
            delete keywords;
            return nullptr;
        }

        Py_DECREF(key_obj);
        Py_DECREF(value_obj);
    }

    delete keywords;

    if (U_FAILURE(status)) {
        Py_DECREF(dict);
        PyErr_SetString(PyExc_RuntimeError, "Failed to retrieve keywords");
        return nullptr;
    }

    return dict;
}

PyGetSetDef Locale_getsetters[] = {
    {const_cast<char*>("bogus"), reinterpret_cast<getter>(Locale_get_bogus), nullptr,
     const_cast<char*>("Whether the locale is bogus"), nullptr},
    {const_cast<char*>("language"), reinterpret_cast<getter>(Locale_get_language), nullptr,
     const_cast<char*>("The locale's ISO-639 language code"), nullptr},
    {const_cast<char*>("country"), reinterpret_cast<getter>(Locale_get_country), nullptr,
     const_cast<char*>("The locale's ISO-3166 country code"), nullptr},
    {const_cast<char*>("variant"), reinterpret_cast<getter>(Locale_get_variant), nullptr,
     const_cast<char*>("The locale's variant code"), nullptr},
    {const_cast<char*>("extensions"), reinterpret_cast<getter>(Locale_get_extensions), nullptr,
     const_cast<char*>("The locale's keywords and values"), nullptr},
    {nullptr, nullptr, nullptr, nullptr, nullptr}
};

PyType_Slot Locale_slots[] = {
    {Py_tp_doc, const_cast<char*>("ICU Locale")},
    {Py_tp_dealloc, reinterpret_cast<void*>(Locale_dealloc)},
    {Py_tp_init, reinterpret_cast<void*>(Locale_init)},
    {Py_tp_new, reinterpret_cast<void*>(Locale_new)},
    {Py_tp_getset, Locale_getsetters},
    {0, nullptr}
};

PyType_Spec Locale_spec = {
    "icu4py.locale.Locale",
    sizeof(LocaleObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    Locale_slots
};

PyMethodDef locale_module_methods[] = {
    {nullptr, nullptr, 0, nullptr}
};

int icu4py_locale_exec(PyObject* m) {
    PyObject* type_obj = PyType_FromModuleAndSpec(m, &Locale_spec, nullptr);
    if (type_obj == nullptr) {
        return -1;
    }

    if (PyModule_AddObject(m, "Locale", type_obj) < 0) {
        Py_DECREF(type_obj);
        return -1;
    }

    return 0;
}

PyModuleDef_Slot locale_slots[] = {
    {Py_mod_exec, reinterpret_cast<void*>(icu4py_locale_exec)},
#ifdef Py_GIL_DISABLED
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, nullptr}
};

static PyModuleDef localemodule = {
    PyModuleDef_HEAD_INIT,
    "icu4py.locale",
    "",
    0,
    locale_module_methods,
    locale_slots,
    nullptr,
    nullptr,
    nullptr,
};

}  // anonymous namespace

PyMODINIT_FUNC PyInit_locale() {
    return PyModuleDef_Init(&localemodule);
}
