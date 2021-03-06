"""
General GL buffer handling
"""

from array import array
from ctypes import byref, sizeof, c_uint, c_ubyte, cast, c_void_p, memmove, POINTER
from typing import List

try:
    import numpy as np
except ImportError:
    np = None
from pyglet import gl

from .util import LoggerMixin


class Buffer(LoggerMixin):

    def __init__(self, data: List=None, structure=gl.GLfloat, size=0, flags=gl.GL_DYNAMIC_STORAGE_BIT):
        self.name = gl.GLuint()
        self.structure = structure
        gl.glCreateBuffers(1, byref(self.name))
        if size == 0 and len(data):
            length = len(data)
            size = length * sizeof(structure)
        else:
            length = size // sizeof(structure)
        self.length = length
        self.size = size
        if isinstance(data, list):
            gl.glNamedBufferStorage(self.name, size, (structure*len(data))(*data), flags)
        elif np and isinstance(data, np.ndarray):
            gl.glNamedBufferStorage(self.name, size, data.ctypes.data, flags)            

    def __len__(self):
        return self.length

    def write(self, data, offset=0):
        gl.glNamedBufferSubData(self.name, offset, len(data)*sizeof(self.structure),
                                (self.structure*len(data))(*data))

    def delete(self):
        gl.glDeleteBuffers(1, (c_uint*1)(self.name))

    def __del__(self):
        try:
            self.delete()
        except ImportError:
            pass
        

class IndexBuffer(Buffer):

    def __init__(self, data: List[int], structure=gl.GLuint):
        self.name = gl.GLuint()
        self.structure = structure
        gl.glGenBuffers(1, byref(self.name))
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.name)
        self.length = len(data)
        self.size = self.length * sizeof(structure)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, self.size, (structure*len(data))(*data),
                        gl.GL_STATIC_DRAW)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    def __enter__(self, *args):
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.name)

    def __exit__(self, *args):
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    def __repr__(self):
        return f"{self.__class__.__name__}(length={self.length})"
