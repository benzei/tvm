"""Node namespace"""
# pylint: disable=unused-import
from __future__ import absolute_import

import ctypes
import sys
from .. import _api_internal
from .node_generic import NodeGeneric, convert_to_node, const
from .base import _LIB, check_call, c_str, py_str, _FFI_MODE

IMPORT_EXCEPT = RuntimeError if _FFI_MODE == "cython" else ImportError
try:
    # pylint: disable=wrong-import-position
    if _FFI_MODE == "ctypes":
        raise ImportError()
    if sys.version_info >= (3, 0):
        from ._cy3.core import _register_node, NodeBase as _NodeBase
    else:
        from ._cy2.core import _register_node, NodeBase as _NodeBase
except IMPORT_EXCEPT:
    # pylint: disable=wrong-import-position
    from ._ctypes.node import _register_node, NodeBase as _NodeBase

class NodeBase(_NodeBase):
    """NodeBase is the base class of all TVM language AST object."""
    def __repr__(self):
        return _api_internal._format_str(self)

    def __dir__(self):
        plist = ctypes.POINTER(ctypes.c_char_p)()
        size = ctypes.c_uint()
        check_call(_LIB.TVMNodeListAttrNames(
            self.handle, ctypes.byref(size), ctypes.byref(plist)))
        names = []
        for i in range(size.value):
            names.append(py_str(plist[i]))
        return names

    def __hash__(self):
        return _api_internal._raw_ptr(self)

    def __eq__(self, other):
        if not isinstance(other, NodeBase):
            return False
        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __reduce__(self):
        return (type(self), (None,), self.__getstate__())

    def __getstate__(self):
        handle = self.handle
        if handle is not None:
            return {'handle': _api_internal._save_json(self)}
        return {'handle': None}

    def __setstate__(self, state):
        # pylint: disable=assigning-non-slot
        handle = state['handle']
        if handle is not None:
            json_str = handle
            other = _api_internal._load_json(json_str)
            self.handle = other.handle
            other.handle = None
        else:
            self.handle = None


def register_node(type_key=None):
    """register node type

    Parameters
    ----------
    type_key : str or cls
        The type key of the node
    """
    node_name = type_key if isinstance(type_key, str) else type_key.__name__

    def register(cls):
        """internal register function"""
        tindex = ctypes.c_int()
        try:
            check_call(_LIB.TVMNodeTypeKey2Index(c_str(node_name), ctypes.byref(tindex)))
            _register_node(tindex.value, cls)
        except AttributeError:
            pass
        return cls

    if isinstance(type_key, str):
        return register
    return register(type_key)