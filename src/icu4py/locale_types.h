#ifndef ICU4PY_LOCALE_TYPES_H
#define ICU4PY_LOCALE_TYPES_H

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <unicode/locid.h>

namespace icu4py {

struct LocaleObject {
    PyObject_HEAD icu::Locale *locale;
};

}  // namespace icu4py

#endif  // ICU4PY_LOCALE_TYPES_H
