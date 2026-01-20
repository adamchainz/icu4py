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

#include "locale_types.h"

namespace {

using icu::MessageFormat;
using icu::UnicodeString;
using icu::Formattable;
using icu::Locale;
using icu::FieldPosition;
using icu::StringPiece;
using icu4py::LocaleObject;

struct ModuleState {
    PyObject* datetime_datetime_type;
    PyObject* datetime_date_type;
    PyObject* datetime_time_type;
    PyObject* decimal_decimal_type;
    PyObject* locale_type;
};

static inline ModuleState* get_module_state(PyObject* module) {
    void* state = PyModule_GetState(module);
    return static_cast<ModuleState*>(state);
}

int icu4py_messageformat_exec(PyObject* m);
int icu4py_messageformat_traverse(PyObject* m, visitproc visit, void* arg);
int icu4py_messageformat_clear(PyObject* m);

PyMethodDef icu4py_messageformat_module_methods[] = {
    {nullptr, nullptr, 0, nullptr}
};

PyModuleDef_Slot icu4py_messageformat_slots[] = {
    {Py_mod_exec, reinterpret_cast<void*>(icu4py_messageformat_exec)},
// On Python 3.13+, declare free-threaded support.
// https://py-free-threading.github.io/porting-extensions/#declaring-free-threaded-support
#ifdef Py_GIL_DISABLED
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, nullptr}
};

static PyModuleDef icu4pymodule = {
    PyModuleDef_HEAD_INIT,
    "icu4py.messageformat",
    "",
    sizeof(ModuleState),
    icu4py_messageformat_module_methods,
    icu4py_messageformat_slots,
    icu4py_messageformat_traverse,
    icu4py_messageformat_clear,
    nullptr,
};

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
    PyObject* locale_obj;
    Py_ssize_t pattern_len;

    static const char* kwlist[] = {"pattern", "locale", nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s#O",
                                     const_cast<char**>(kwlist),
                                     &pattern, &pattern_len, &locale_obj)) {
        return -1;
    }

#if PY_VERSION_HEX < 0x030B0000
    PyObject* module = _PyType_GetModuleByDef(Py_TYPE(self), &icu4pymodule);
#else
    PyObject* module = PyType_GetModuleByDef(Py_TYPE(self), &icu4pymodule);
#endif
    if (module == nullptr) {
        return -1;
    }
    ModuleState* mod_state = get_module_state(module);

    UErrorCode status = U_ZERO_ERROR;
    UnicodeString upattern = UnicodeString::fromUTF8(StringPiece(pattern, pattern_len));
    Locale locale;

    if (PyUnicode_Check(locale_obj)) {
        const char* locale_str = PyUnicode_AsUTF8(locale_obj);
        if (locale_str == nullptr) {
            return -1;
        }
        locale = Locale(locale_str);
    } else {
        int is_locale = PyObject_IsInstance(locale_obj, mod_state->locale_type);
        if (is_locale == -1) {
            return -1;
        }
        if (is_locale == 0) {
            PyErr_SetString(PyExc_TypeError, "locale must be a string or Locale object");
            return -1;
        }

        LocaleObject* locale_pyobj = reinterpret_cast<LocaleObject*>(locale_obj);
        if (locale_pyobj->locale == nullptr) {
            PyErr_SetString(PyExc_ValueError, "Locale object has null internal locale");
            return -1;
        }
        locale = *locale_pyobj->locale;
    }

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
                PyErr_Format(PyExc_ValueError, "Failed to create Formattable from overflowed int: %s",
                              u_errorName(status));
                return false;
            }
            return true;
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
          if (dbl_val == -1.0 && PyErr_Occurred()) {
              return false;
          }
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

          PyObject* min_time = PyObject_GetAttrString(state->datetime_time_type, "min");
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

bool dict_to_parallel_arrays(PyObject* dict, ModuleState* mod_state, UnicodeString*& names,
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

#if PY_VERSION_HEX < 0x030B0000
    PyObject* module = _PyType_GetModuleByDef(Py_TYPE(self), &icu4pymodule);
#else
    PyObject* module = PyType_GetModuleByDef(Py_TYPE(self), &icu4pymodule);
#endif
    if (module == nullptr) {
        return nullptr;
    }
    ModuleState* mod_state = get_module_state(module);

    UnicodeString* argumentNames = nullptr;
    Formattable* arguments = nullptr;
    int32_t count = 0;

    if (!dict_to_parallel_arrays(params_dict, mod_state, argumentNames, arguments, count)) {
        return nullptr;
    }

    auto names_guard = std::unique_ptr<UnicodeString[]>(argumentNames);
    auto values_guard = std::unique_ptr<Formattable[]>(arguments);

    UErrorCode status = U_ZERO_ERROR;
    UnicodeString result;

    // ICU objects need external synchronization
#ifdef Py_GIL_DISABLED
    Py_BEGIN_CRITICAL_SECTION(self);
#endif

    if (count == 0) {
        FieldPosition field_pos;
        result = self->formatter->format(nullptr, 0, result, field_pos, status);
    } else {
        result = self->formatter->format(argumentNames, arguments, count, result, status);
    }

#ifdef Py_GIL_DISABLED
    Py_END_CRITICAL_SECTION();
#endif

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

PyType_Slot MessageFormat_slots[] = {
    {Py_tp_doc, const_cast<char*>("ICU MessageFormat")},
    {Py_tp_dealloc, reinterpret_cast<void*>(MessageFormat_dealloc)},
    {Py_tp_init, reinterpret_cast<void*>(MessageFormat_init)},
    {Py_tp_new, reinterpret_cast<void*>(MessageFormat_new)},
    {Py_tp_methods, MessageFormat_methods},
    {0, nullptr}
};

PyType_Spec MessageFormat_spec = {
    "icu4py.messageformat.MessageFormat",
    sizeof(MessageFormatObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    MessageFormat_slots
};

int icu4py_messageformat_exec(PyObject* m) {
    PyObject* type_obj = PyType_FromModuleAndSpec(m, &MessageFormat_spec, nullptr);
    if (type_obj == nullptr) {
        return -1;
    }

    if (PyModule_AddObject(m, "MessageFormat", type_obj) < 0) {
        Py_DECREF(type_obj);
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

    PyObject* locale_module = PyImport_ImportModule("icu4py.locale");
    if (locale_module == nullptr) {
        return -1;
    }

    state->locale_type = PyObject_GetAttrString(locale_module, "Locale");
    Py_DECREF(locale_module);

    if (state->locale_type == nullptr) {
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
    Py_VISIT(state->locale_type);
    return 0;
}

int icu4py_messageformat_clear(PyObject* m) {
    ModuleState* state = get_module_state(m);
    Py_CLEAR(state->datetime_datetime_type);
    Py_CLEAR(state->datetime_date_type);
    Py_CLEAR(state->datetime_time_type);
    Py_CLEAR(state->decimal_decimal_type);
    Py_CLEAR(state->locale_type);
    return 0;
}

}  // anonymous namespace

PyMODINIT_FUNC PyInit_messageformat() {
    return PyModuleDef_Init(&icu4pymodule);
}
