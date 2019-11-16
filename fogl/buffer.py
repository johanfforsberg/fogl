"""
General GL buffer handling
"""

from ctypes import byref, sizeof

from pyglet import gl

from .util import LoggerMixin


class Buffer(LoggerMixin):

    def __init__(self, data=None, structure=gl.GLfloat, size=0):
        self.name = gl.GLuint()
        self.structure = structure
        gl.glCreateBuffers(1, byref(self.name))
        if size == 0 and data:
            length = len(data)
            size = length * sizeof(structure)
        else:
            length = size // sizeof(structure)
        self.length = length
        self.size = size
        gl.glNamedBufferStorage(self.name, size, (structure*len(data))(*data),
                                gl.GL_DYNAMIC_STORAGE_BIT)

    def __len__(self):
        return self.length

    def write(self, data, offset=0):
        gl.glNamedBufferSubData(self.name, offset, len(data)*sizeof(self.structure),
                                (self.structure*len(data))(*data))


class IndexBuffer(Buffer):

    def __init__(self, data, structure=gl.GLuint):
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
