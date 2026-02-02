#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <unicode/brkiter.h>
#include <unicode/locid.h>
#include <unicode/unistr.h>
#include <unicode/utypes.h>
#include <unicode/stringpiece.h>

#include <memory>

#include "locale_types.h"

namespace {

using icu::BreakIterator;
using icu::Locale;
using icu::UnicodeString;
using icu::StringPiece;
using icu4py::LocaleObject;

struct ModuleState {
    PyObject* locale_type;
    PyObject* segment_iterator_type;
    PyObject* string_iterator_type;
};

static inline ModuleState* get_module_state(PyObject* module) {
    void* state = PyModule_GetState(module);
    return static_cast<ModuleState*>(state);
}

int icu4py_breakers_exec(PyObject* m);
int icu4py_breakers_traverse(PyObject* m, visitproc visit, void* arg);
int icu4py_breakers_clear(PyObject* m);

extern PyModuleDef breakersmodule;

struct BreakerObject {
    PyObject_HEAD
    BreakIterator* breaker;
    UnicodeString text;
};

struct SegmentIteratorObject {
    PyObject_HEAD
    BreakerObject* breaker;
    int32_t current_pos;
};

struct StringIteratorObject {
    PyObject_HEAD
    BreakerObject* breaker;
    int32_t current_pos;
};

void BaseBreaker_dealloc(BreakerObject* self) {
    delete self->breaker;
    self->text.~UnicodeString();
    Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyObject* BaseBreaker_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    auto* self = reinterpret_cast<BreakerObject*>(type->tp_alloc(type, 0));
    if (self != nullptr) {
        self->breaker = nullptr;
        new (&self->text) UnicodeString();
    }
    return reinterpret_cast<PyObject*>(self);
}

int Breaker_init_impl(BreakerObject* self, PyObject* args, PyObject* kwds,
                      BreakIterator* (*factory)(const Locale&, UErrorCode&)) {
    const char* text;
    Py_ssize_t text_len;
    PyObject* locale_obj;

    static const char* kwlist[] = {"text", "locale", nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s#O",
                                     const_cast<char**>(kwlist),
                                     &text, &text_len, &locale_obj)) {
        return -1;
    }

#if PY_VERSION_HEX < 0x030B0000
    PyObject* module = _PyType_GetModuleByDef(Py_TYPE(self), &breakersmodule);
#else
    PyObject* module = PyType_GetModule(Py_TYPE(self));
#endif
    if (module == nullptr) {
        return -1;
    }
    ModuleState* mod_state = get_module_state(module);

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

    UErrorCode status = U_ZERO_ERROR;
    self->breaker = factory(locale, status);

    if (U_FAILURE(status)) {
        delete self->breaker;
        self->breaker = nullptr;
        PyErr_Format(PyExc_RuntimeError, "Failed to create BreakIterator: %s",
                     u_errorName(status));
        return -1;
    }

    self->text = UnicodeString::fromUTF8(StringPiece(text, text_len));
    self->breaker->setText(self->text);

    return 0;
}

void SegmentIterator_dealloc(SegmentIteratorObject* self) {
    Py_XDECREF(self->breaker);
    Py_TYPE(self)->tp_free(reinterpret_cast<PyObject*>(self));
}

PyObject* SegmentIterator_iter(PyObject* self) {
    Py_INCREF(self);
    return self;
}

PyObject* SegmentIterator_iternext(SegmentIteratorObject* self) {
    int32_t next_pos;

#ifdef Py_GIL_DISABLED
    Py_BEGIN_CRITICAL_SECTION(self->breaker);
#endif

    next_pos = self->breaker->breaker->next();

#ifdef Py_GIL_DISABLED
    Py_END_CRITICAL_SECTION();
#endif

    if (next_pos == BreakIterator::DONE) {
        return nullptr;
    }

    int32_t start = self->current_pos;
    self->current_pos = next_pos;

    return Py_BuildValue("(ii)", start, next_pos);
}

PyType_Slot SegmentIterator_slots[] = {
    {Py_tp_dealloc, reinterpret_cast<void*>(SegmentIterator_dealloc)},
    {Py_tp_iter, reinterpret_cast<void*>(SegmentIterator_iter)},
    {Py_tp_iternext, reinterpret_cast<void*>(SegmentIterator_iternext)},
    {0, nullptr}
};

PyType_Spec SegmentIterator_spec = {
    "icu4py.breakers._SegmentIterator",
    sizeof(SegmentIteratorObject),
    0,
    Py_TPFLAGS_DEFAULT,
    SegmentIterator_slots
};

void StringIterator_dealloc(StringIteratorObject* self) {
    Py_XDECREF(self->breaker);
    Py_TYPE(self)->tp_free(reinterpret_cast<void*>(self));
}

PyObject* StringIterator_iter(PyObject* self) {
    Py_INCREF(self);
    return self;
}

PyObject* StringIterator_iternext(StringIteratorObject* self) {
    int32_t next_pos;

#ifdef Py_GIL_DISABLED
    Py_BEGIN_CRITICAL_SECTION(self->breaker);
#endif

    next_pos = self->breaker->breaker->next();

#ifdef Py_GIL_DISABLED
    Py_END_CRITICAL_SECTION();
#endif

    if (next_pos == BreakIterator::DONE) {
        return nullptr;
    }

    UnicodeString segment;
    self->breaker->text.extractBetween(self->current_pos, next_pos, segment);
    self->current_pos = next_pos;

    std::string utf8;
    segment.toUTF8String(utf8);
    return PyUnicode_FromStringAndSize(utf8.c_str(), utf8.size());
}

PyType_Slot StringIterator_slots[] = {
    {Py_tp_dealloc, reinterpret_cast<void*>(StringIterator_dealloc)},
    {Py_tp_iter, reinterpret_cast<void*>(StringIterator_iter)},
    {Py_tp_iternext, reinterpret_cast<void*>(StringIterator_iternext)},
    {0, nullptr}
};

PyType_Spec StringIterator_spec = {
    "icu4py.breakers._StringIterator",
    sizeof(StringIteratorObject),
    0,
    Py_TPFLAGS_DEFAULT,
    StringIterator_slots
};

PyObject* Breaker_segments(BreakerObject* self, PyObject* Py_UNUSED(args)) {
#if PY_VERSION_HEX < 0x030B0000
    PyObject* module = _PyType_GetModuleByDef(Py_TYPE(self), &breakersmodule);
#else
    PyObject* module = PyType_GetModule(Py_TYPE(self));
#endif
    if (module == nullptr) {
        return nullptr;
    }

    ModuleState* state = get_module_state(module);

    auto* iter = reinterpret_cast<SegmentIteratorObject*>(
        PyObject_CallNoArgs(state->segment_iterator_type));

    if (iter == nullptr) {
        return nullptr;
    }

    Py_INCREF(self);
    iter->breaker = self;

#ifdef Py_GIL_DISABLED
    Py_BEGIN_CRITICAL_SECTION(self);
#endif

    self->breaker->first();
    iter->current_pos = 0;

#ifdef Py_GIL_DISABLED
    Py_END_CRITICAL_SECTION();
#endif

    return reinterpret_cast<PyObject*>(iter);
}

PyObject* BaseBreaker_iter(BreakerObject* self) {
#if PY_VERSION_HEX < 0x030B0000
    PyObject* module = _PyType_GetModuleByDef(Py_TYPE(self), &breakersmodule);
#else
    PyObject* module = PyType_GetModule(Py_TYPE(self));
#endif
    if (module == nullptr) {
        return nullptr;
    }

    ModuleState* state = get_module_state(module);

    auto* iter = reinterpret_cast<StringIteratorObject*>(
        PyObject_CallNoArgs(state->string_iterator_type));

    if (iter == nullptr) {
        return nullptr;
    }

    Py_INCREF(self);
    iter->breaker = self;

#ifdef Py_GIL_DISABLED
    Py_BEGIN_CRITICAL_SECTION(self);
#endif

    self->breaker->first();
    iter->current_pos = 0;

#ifdef Py_GIL_DISABLED
    Py_END_CRITICAL_SECTION();
#endif

    return reinterpret_cast<PyObject*>(iter);
}

PyMethodDef Breaker_methods[] = {
    {"segments", reinterpret_cast<PyCFunction>(Breaker_segments), METH_NOARGS,
     "Iterate over (start, end) segment positions"},
    {nullptr, nullptr, 0, nullptr}
};

int BaseBreaker_init(BreakerObject* self, PyObject* args, PyObject* kwds) {
    const char* text;
    Py_ssize_t text_len;
    PyObject* locale_obj;

    static const char* kwlist[] = {"text", "locale", nullptr};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s#O",
                                     const_cast<char**>(kwlist),
                                     &text, &text_len, &locale_obj)) {
        return -1;
    }

    PyTypeObject* type = Py_TYPE(self);
    PyTypeObject* base_type = nullptr;

#if PY_VERSION_HEX < 0x030B0000
    PyObject* module = _PyType_GetModuleByDef(type, &breakersmodule);
#else
    PyObject* module = PyType_GetModule(type);
#endif
    if (module == nullptr) {
        return -1;
    }

    base_type = reinterpret_cast<PyTypeObject*>(PyObject_GetAttrString(module, "BaseBreaker"));
    if (base_type == nullptr) {
        return -1;
    }

    int is_base = (type == base_type);
    Py_DECREF(base_type);

    if (is_base) {
        PyErr_SetString(PyExc_TypeError, "Cannot instantiate BaseBreaker directly");
        return -1;
    }

    PyErr_SetString(PyExc_TypeError, "Subclass must implement __init__");
    return -1;
}

PyType_Slot BaseBreaker_slots[] = {
    {Py_tp_doc, const_cast<char*>("Base break iterator")},
    {Py_tp_dealloc, reinterpret_cast<void*>(BaseBreaker_dealloc)},
    {Py_tp_new, reinterpret_cast<void*>(BaseBreaker_new)},
    {Py_tp_init, reinterpret_cast<void*>(BaseBreaker_init)},
    {Py_tp_iter, reinterpret_cast<void*>(BaseBreaker_iter)},
    {Py_tp_methods, Breaker_methods},
    {0, nullptr}
};

PyType_Spec BaseBreaker_spec = {
    "icu4py.breakers.BaseBreaker",
    sizeof(BreakerObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    BaseBreaker_slots
};

int CharacterBreaker_init(BreakerObject* self, PyObject* args, PyObject* kwds) {
    return Breaker_init_impl(self, args, kwds, BreakIterator::createCharacterInstance);
}

PyType_Slot CharacterBreaker_slots[] = {
    {Py_tp_doc, const_cast<char*>("Character break iterator")},
    {Py_tp_init, reinterpret_cast<void*>(CharacterBreaker_init)},
    {0, nullptr}
};

PyType_Spec CharacterBreaker_spec = {
    "icu4py.breakers.CharacterBreaker",
    sizeof(BreakerObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    CharacterBreaker_slots
};

int WordBreaker_init(BreakerObject* self, PyObject* args, PyObject* kwds) {
    return Breaker_init_impl(self, args, kwds, BreakIterator::createWordInstance);
}

PyType_Slot WordBreaker_slots[] = {
    {Py_tp_doc, const_cast<char*>("Word break iterator")},
    {Py_tp_init, reinterpret_cast<void*>(WordBreaker_init)},
    {0, nullptr}
};

PyType_Spec WordBreaker_spec = {
    "icu4py.breakers.WordBreaker",
    sizeof(BreakerObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    WordBreaker_slots
};

int LineBreaker_init(BreakerObject* self, PyObject* args, PyObject* kwds) {
    return Breaker_init_impl(self, args, kwds, BreakIterator::createLineInstance);
}

PyType_Slot LineBreaker_slots[] = {
    {Py_tp_doc, const_cast<char*>("Line break iterator")},
    {Py_tp_init, reinterpret_cast<void*>(LineBreaker_init)},
    {0, nullptr}
};

PyType_Spec LineBreaker_spec = {
    "icu4py.breakers.LineBreaker",
    sizeof(BreakerObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    LineBreaker_slots
};

int SentenceBreaker_init(BreakerObject* self, PyObject* args, PyObject* kwds) {
    return Breaker_init_impl(self, args, kwds, BreakIterator::createSentenceInstance);
}

PyType_Slot SentenceBreaker_slots[] = {
    {Py_tp_doc, const_cast<char*>("Sentence break iterator")},
    {Py_tp_init, reinterpret_cast<void*>(SentenceBreaker_init)},
    {0, nullptr}
};

PyType_Spec SentenceBreaker_spec = {
    "icu4py.breakers.SentenceBreaker",
    sizeof(BreakerObject),
    0,
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    SentenceBreaker_slots
};

PyMethodDef breakers_module_methods[] = {
    {nullptr, nullptr, 0, nullptr}
};

PyModuleDef_Slot breakers_slots[] = {
    {Py_mod_exec, reinterpret_cast<void*>(icu4py_breakers_exec)},
#ifdef Py_GIL_DISABLED
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, nullptr}
};

PyModuleDef breakersmodule = {
    PyModuleDef_HEAD_INIT,
    "icu4py.breakers",
    "",
    sizeof(ModuleState),
    breakers_module_methods,
    breakers_slots,
    icu4py_breakers_traverse,
    icu4py_breakers_clear,
    nullptr,
};

int icu4py_breakers_exec(PyObject* m) {
    PyObject* segment_iter_type = PyType_FromModuleAndSpec(m, &SegmentIterator_spec, nullptr);
    if (segment_iter_type == nullptr) {
        return -1;
    }
    if (PyModule_AddObject(m, "_SegmentIterator", segment_iter_type) < 0) {
        Py_DECREF(segment_iter_type);
        return -1;
    }

    PyObject* string_iter_type = PyType_FromModuleAndSpec(m, &StringIterator_spec, nullptr);
    if (string_iter_type == nullptr) {
        return -1;
    }
    if (PyModule_AddObject(m, "_StringIterator", string_iter_type) < 0) {
        Py_DECREF(string_iter_type);
        return -1;
    }

    PyObject* base_type = PyType_FromModuleAndSpec(m, &BaseBreaker_spec, nullptr);
    if (base_type == nullptr) {
        return -1;
    }
    if (PyModule_AddObject(m, "BaseBreaker", base_type) < 0) {
        Py_DECREF(base_type);
        return -1;
    }

    PyObject* bases = PyTuple_Pack(1, base_type);
    if (bases == nullptr) {
        return -1;
    }

    PyObject* char_type = PyType_FromModuleAndSpec(m, &CharacterBreaker_spec, bases);
    Py_DECREF(bases);
    if (char_type == nullptr) {
        return -1;
    }
    if (PyModule_AddObject(m, "CharacterBreaker", char_type) < 0) {
        Py_DECREF(char_type);
        return -1;
    }

    bases = PyTuple_Pack(1, base_type);
    if (bases == nullptr) {
        return -1;
    }

    PyObject* word_type = PyType_FromModuleAndSpec(m, &WordBreaker_spec, bases);
    Py_DECREF(bases);
    if (word_type == nullptr) {
        return -1;
    }
    if (PyModule_AddObject(m, "WordBreaker", word_type) < 0) {
        Py_DECREF(word_type);
        return -1;
    }

    bases = PyTuple_Pack(1, base_type);
    if (bases == nullptr) {
        return -1;
    }

    PyObject* line_type = PyType_FromModuleAndSpec(m, &LineBreaker_spec, bases);
    Py_DECREF(bases);
    if (line_type == nullptr) {
        return -1;
    }
    if (PyModule_AddObject(m, "LineBreaker", line_type) < 0) {
        Py_DECREF(line_type);
        return -1;
    }

    bases = PyTuple_Pack(1, base_type);
    if (bases == nullptr) {
        return -1;
    }

    PyObject* sentence_type = PyType_FromModuleAndSpec(m, &SentenceBreaker_spec, bases);
    Py_DECREF(bases);
    if (sentence_type == nullptr) {
        return -1;
    }
    if (PyModule_AddObject(m, "SentenceBreaker", sentence_type) < 0) {
        Py_DECREF(sentence_type);
        return -1;
    }

    ModuleState* state = get_module_state(m);

    state->segment_iterator_type = segment_iter_type;
    Py_INCREF(state->segment_iterator_type);

    state->string_iterator_type = string_iter_type;
    Py_INCREF(state->string_iterator_type);

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

int icu4py_breakers_traverse(PyObject* m, visitproc visit, void* arg) {
    ModuleState* state = get_module_state(m);
    Py_VISIT(state->locale_type);
    Py_VISIT(state->segment_iterator_type);
    Py_VISIT(state->string_iterator_type);
    return 0;
}

int icu4py_breakers_clear(PyObject* m) {
    ModuleState* state = get_module_state(m);
    Py_CLEAR(state->locale_type);
    Py_CLEAR(state->segment_iterator_type);
    Py_CLEAR(state->string_iterator_type);
    return 0;
}

}  // anonymous namespace

PyMODINIT_FUNC PyInit_breakers() {
    return PyModuleDef_Init(&breakersmodule);
}
