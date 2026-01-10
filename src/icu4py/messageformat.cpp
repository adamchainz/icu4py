#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <unicode/msgfmt.h>
#include <unicode/unistr.h>
#include <unicode/fmtable.h>
#include <unicode/locid.h>
#include <unicode/parsepos.h>
#include <unicode/ustring.h>
#include <unicode/utypes.h>

#include <cstring>
#include <memory>
#include <limits>

namespace {

using icu::MessageFormat;
using icu::UnicodeString;
using icu::Formattable;
using icu::Locale;
using icu::FieldPosition;
using icu::StringPiece;

struct ModuleState {
    PyObject* datetime_datetime_type;
    PyObject* datetime_date_type;
    PyObject* datetime_time_type;
    PyObject* decimal_decimal_type;
};

static inline ModuleState* get_module_state(PyObject* module) {
    void* state = PyModule_GetState(module);
    return static_cast<ModuleState*>(state);
}

struct MessageFormatObject {
    PyObject_HEAD
    MessageFormat* formatter;
};

void MessageFormat_dealloc(MessageFormatObject* self) {
    delete self->formatter;
    Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyObject* MessageFormat_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    auto* self = reinterpret_cast<MessageFormatObject*>(type->tp_alloc(type, 0));
    if (self != nullptr) {
        self->formatter = nullptr;
    }
    return reinterpret_cast<PyObject*>(self);
}

int MessageFormat_init(MessageFormatObject* self, PyObject* args, PyObject* kwds) {
    const char* pattern;
    const char* locale_str;
    Py_ssize_t pattern_len;

    static const char* kwlist[] = {"pattern", "locale", nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s#s",
                                     const_cast<char**>(kwlist),
                                     &pattern, &pattern_len, &locale_str)) {
        return -1;
    }

    UErrorCode status = U_ZERO_ERROR;
    UnicodeString upattern = UnicodeString::fromUTF8(StringPiece(pattern, pattern_len));
    Locale locale(locale_str);

    self->formatter = new MessageFormat(upattern, locale, status);

    if (U_FAILURE(status)) {
        delete self->formatter;
        self->formatter = nullptr;
        PyErr_Format(PyExc_ValueError, "Failed to create MessageFormat: %s",
                     u_errorName(status));
        return -1;
    }

    return 0;
}

bool pyobject_to_formattable(PyObject* obj, Formattable& formattable, ModuleState* state) {
  if (PyLong_Check(obj)) {
      int overflow;
      long long long_val = PyLong_AsLongLongAndOverflow(obj, &overflow);
      if (overflow != 0) {
          PyErr_SetString(PyExc_OverflowError, "Integer value out of range for int64");
          return false;
      }
      if (long_val == -1 && PyErr_Occurred()) {
          return false;
      }
      formattable = Formattable(static_cast<int64_t>(long_val));
      return true;
  }

    if (PyUnicode_Check(obj)) {
        Py_ssize_t size;
        const char* str_val = PyUnicode_AsUTF8AndSize(obj, &size);
        if (str_val == nullptr) {
            return false;
        }
        formattable = Formattable(UnicodeString::fromUTF8(StringPiece(str_val, size)));
        return true;
    }

    if (PyFloat_Check(obj)) {
        double dbl_val = PyFloat_AsDouble(obj);
        formattable = Formattable(dbl_val);
        return true;
    }

    int is_decimal = PyObject_IsInstance(obj, state->decimal_decimal_type);
    if (is_decimal == -1) {
        return false;
    } else if (is_decimal == 1) {
        PyObject* str_obj = PyObject_Str(obj);
        if (str_obj == nullptr) {
            return false;
        }
        Py_ssize_t size;
        const char* str_val = PyUnicode_AsUTF8AndSize(str_obj, &size);
        if (str_val == nullptr) {
            Py_DECREF(str_obj);
            return false;
        }
        UErrorCode status = U_ZERO_ERROR;
        formattable = Formattable(StringPiece(str_val, size), status);
        Py_DECREF(str_obj);
        if (U_FAILURE(status)) {
            PyErr_Format(PyExc_ValueError, "Failed to create Formattable from Decimal: %s",
                          u_errorName(status));
            return false;
        }
        return true;
    }

    int is_datetime = PyObject_IsInstance(obj, state->datetime_datetime_type);
    if (is_datetime == -1) {
        return false;
    } else if (is_datetime == 1) {
        PyObject* timestamp = PyObject_CallMethod(obj, "timestamp", nullptr);
        if (timestamp == nullptr) {
            return false;
        }
        double timestamp_seconds = PyFloat_AsDouble(timestamp);
        Py_DECREF(timestamp);
        if (timestamp_seconds == -1.0 && PyErr_Occurred()) {
            return false;
        }
        UDate udate = timestamp_seconds * 1000.0;
        formattable = Formattable(udate, Formattable::kIsDate);
        return true;
    }

    int is_date = PyObject_IsInstance(obj, state->datetime_date_type);
    if (is_date == -1) {
        return false;
    } else if (is_date == 1) {
        PyObject* combine = PyObject_GetAttrString(state->datetime_datetime_type, "combine");
        if (combine == nullptr) {
            return false;
        }

        if (state->datetime_time_type == nullptr) {
            Py_DECREF(combine);
            return false;
        }

        PyObject* min_time = PyObject_CallNoArgs(state->datetime_time_type);
        if (min_time == nullptr) {
            Py_DECREF(combine);
            return false;
        }

        PyObject* dt = PyObject_CallFunctionObjArgs(combine, obj, min_time, nullptr);
        Py_DECREF(combine);
        Py_DECREF(min_time);
        if (dt == nullptr) {
            return false;
        }

        PyObject* timestamp = PyObject_CallMethod(dt, "timestamp", nullptr);
        Py_DECREF(dt);
        if (timestamp == nullptr) {
            return false;
        }
        double timestamp_seconds = PyFloat_AsDouble(timestamp);
        Py_DECREF(timestamp);
        if (timestamp_seconds == -1.0 && PyErr_Occurred()) {
            return false;
        }
        UDate udate = timestamp_seconds * 1000.0;
        formattable = Formattable(udate, Formattable::kIsDate);
        return true;
    }

    PyErr_SetString(PyExc_TypeError, "Parameter values must be int, float, str, Decimal, datetime, or date");
    return false;
}

bool dict_to_parallel_arrays(PyObject* dict, UnicodeString*& names,
                             Formattable*& values, int32_t& count) {
    if (!PyDict_Check(dict)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be a dictionary");
        return false;
    }

    count = static_cast<int32_t>(PyDict_Size(dict));
    if (count == 0) {
        names = nullptr;
        values = nullptr;
        return true;
    }

    auto names_ptr = std::make_unique<UnicodeString[]>(count);
    auto values_ptr = std::make_unique<Formattable[]>(count);

    Py_ssize_t pos = 0;
    PyObject* key;
    PyObject* value;
    int32_t i = 0;
    bool err = false;

#ifdef Py_GIL_DISABLED
    Py_BEGIN_CRITICAL_SECTION(dict);
#endif
    while (PyDict_Next(dict, &pos, &key, &value)) {
        // Ensure we don't exceed allocated space
        if (i >= count) {
            PyErr_SetString(PyExc_RuntimeError, "Dictionary size changed during iteration");
            err = true;
            break;
        }

        if (key == nullptr) {
            PyErr_SetString(PyExc_TypeError, "NULL key in dictionary");
            err = true;
            break;
        }
        if (value == nullptr) {
            PyErr_SetString(PyExc_TypeError, "NULL value in dictionary");
            err = true;
            break;
        }

        Py_ssize_t key_size;
        const char* key_str = PyUnicode_AsUTF8AndSize(key, &key_size);
        if (key_str == nullptr) {
            PyErr_SetString(PyExc_TypeError, "Dictionary keys must be strings");
            err = true;
            break;
        }
        names_ptr[i] = UnicodeString::fromUTF8(StringPiece(key_str, key_size));

        PyObject* module = PyImport_ImportModule("icu4py.messageformat");
        if (module == nullptr) {
            err = true;
            break;
        }
        ModuleState* mod_state = get_module_state(module);
        Py_DECREF(module);

        if (!pyobject_to_formattable(value, values_ptr[i], mod_state)) {
            if (!PyErr_Occurred()) {
                PyErr_SetString(PyExc_TypeError, "Failed to convert dictionary value to Formattable");
            }
            err = true;
            break;
        }
        ++i;
    }
#ifdef Py_GIL_DISABLED
    Py_END_CRITICAL_SECTION();
#endif
    if (err) {
        return false;
    }

    names = names_ptr.release();
    values = values_ptr.release();
    return true;
}

PyObject* MessageFormat_format(MessageFormatObject* self, PyObject* args) {
    PyObject* params_dict;

    if (!PyArg_ParseTuple(args, "O!", &PyDict_Type, &params_dict)) {
        return nullptr;
    }

    UnicodeString* argumentNames = nullptr;
    Formattable* arguments = nullptr;
    int32_t count = 0;

    if (!dict_to_parallel_arrays(params_dict, argumentNames, arguments, count)) {
        return nullptr;
    }

    auto names_guard = std::unique_ptr<UnicodeString[]>(argumentNames);
    auto values_guard = std::unique_ptr<Formattable[]>(arguments);

    UErrorCode status = U_ZERO_ERROR;
    UnicodeString result;

    if (count == 0) {
        FieldPosition field_pos;
        result = self->formatter->format(nullptr, 0, result, field_pos, status);
    } else {
        result = self->formatter->format(argumentNames, arguments, count, result, status);
    }

    if (U_FAILURE(status)) {
        PyErr_Format(PyExc_RuntimeError, "Failed to format message: %s",
                     u_errorName(status));
        return nullptr;
    }

    std::string utf8;
    result.toUTF8String(utf8);
    return PyUnicode_FromStringAndSize(utf8.c_str(), utf8.size());
}

PyMethodDef MessageFormat_methods[] = {
    {"format", reinterpret_cast<PyCFunction>(MessageFormat_format), METH_VARARGS,
     "Format the message with given parameters"},
    {nullptr, nullptr, 0, nullptr}
};

PyTypeObject MessageFormatType = {
    PyVarObject_HEAD_INIT(nullptr, 0)
    "icu4py.messageformat.MessageFormat", /* tp_name */
    sizeof(MessageFormatObject), /* tp_basicsize */
    0, /* tp_itemsize */
    reinterpret_cast<destructor>(MessageFormat_dealloc), /* tp_dealloc */
    0, /* tp_vectorcall_offset */
    nullptr, /* tp_getattr */
    nullptr, /* tp_setattr */
    nullptr, /* tp_as_async */
    nullptr, /* tp_repr */
    nullptr, /* tp_as_number */
    nullptr, /* tp_as_sequence */
    nullptr, /* tp_as_mapping */
    nullptr, /* tp_hash */
    nullptr, /* tp_call */
    nullptr, /* tp_str */
    nullptr, /* tp_getattro */
    nullptr, /* tp_setattro */
    nullptr, /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT, /* tp_flags */
    "ICU MessageFormat", /* tp_doc */
    nullptr, /* tp_traverse */
    nullptr, /* tp_clear */
    nullptr, /* tp_richcompare */
    0, /* tp_weaklistoffset */
    nullptr, /* tp_iter */
    nullptr, /* tp_iternext */
    MessageFormat_methods, /* tp_methods */
    nullptr, /* tp_members */
    nullptr, /* tp_getset */
    nullptr, /* tp_base */
    nullptr, /* tp_dict */
    nullptr, /* tp_descr_get */
    nullptr, /* tp_descr_set */
    0, /* tp_dictoffset */
    reinterpret_cast<initproc>(MessageFormat_init), /* tp_init */
    nullptr, /* tp_alloc */
    MessageFormat_new, /* tp_new */
};

int icu4py_messageformat_exec(PyObject* m) {
    if (PyType_Ready(&MessageFormatType) < 0) {
        return -1;
    }

    Py_INCREF(&MessageFormatType);
    if (PyModule_AddObject(m, "MessageFormat",
                          reinterpret_cast<PyObject*>(&MessageFormatType)) < 0) {
        Py_DECREF(&MessageFormatType);
        return -1;
    }

    ModuleState* state = get_module_state(m);

    PyObject* datetime_module = PyImport_ImportModule("datetime");
    if (datetime_module == nullptr) {
        return -1;
    }

    state->datetime_datetime_type = PyObject_GetAttrString(datetime_module, "datetime");
    state->datetime_date_type = PyObject_GetAttrString(datetime_module, "date");
    state->datetime_time_type = PyObject_GetAttrString(datetime_module, "time");
    Py_DECREF(datetime_module);

    if (state->datetime_datetime_type == nullptr ||
        state->datetime_date_type == nullptr ||
        state->datetime_time_type == nullptr) {
        return -1;
    }

    PyObject* decimal_module = PyImport_ImportModule("decimal");
    if (decimal_module == nullptr) {
        return -1;
    }

    state->decimal_decimal_type = PyObject_GetAttrString(decimal_module, "Decimal");
    Py_DECREF(decimal_module);

    if (state->decimal_decimal_type == nullptr) {
        return -1;
    }

    return 0;
}

int icu4py_messageformat_traverse(PyObject* m, visitproc visit, void* arg) {
    ModuleState* state = get_module_state(m);
    Py_VISIT(state->datetime_datetime_type);
    Py_VISIT(state->datetime_date_type);
    Py_VISIT(state->datetime_time_type);
    Py_VISIT(state->decimal_decimal_type);
    return 0;
}

int icu4py_messageformat_clear(PyObject* m) {
    ModuleState* state = get_module_state(m);
    Py_CLEAR(state->datetime_datetime_type);
    Py_CLEAR(state->datetime_date_type);
    Py_CLEAR(state->datetime_time_type);
    Py_CLEAR(state->decimal_decimal_type);
    return 0;
}

PyModuleDef_Slot icu4py_messageformat_slots[] = {
    {Py_mod_exec, reinterpret_cast<void*>(icu4py_messageformat_exec)},
#ifdef Py_GIL_DISABLED
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, nullptr}
};

PyMethodDef icu4py_messageformat_module_methods[] = {
    {nullptr, nullptr, 0, nullptr}
};

static PyModuleDef icumodule = {
    PyModuleDef_HEAD_INIT,
    "icu4py.messageformat", /* m_name */
    "", /* m_doc */
    sizeof(ModuleState), /* m_size */
    icu4py_messageformat_module_methods, /* m_methods */
    icu4py_messageformat_slots, /* m_slots */
    icu4py_messageformat_traverse, /* m_traverse */
    icu4py_messageformat_clear, /* m_clear */
    nullptr, /* m_free */
};

}  // anonymous namespace

PyMODINIT_FUNC PyInit_messageformat() {
    return PyModuleDef_Init(&icumodule);
}
