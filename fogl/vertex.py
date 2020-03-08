"""
Handling of GL vertex (attribute) data, such as 3D models.
"""


from abc import ABCMeta
from ctypes import Structure, sizeof
from typing import List, Tuple

from pyglet import gl

from .buffer import Buffer, IndexBuffer
from .util import LoggerMixin


# mapping from GL types to the corresponding ctypes types
gltypes = {
    gl.GL_FLOAT: gl.GLfloat,
    gl.GL_DOUBLE: gl.GLdouble,
    gl.GL_INT: gl.GLint,
    gl.GL_BYTE: gl.GLbyte,
    gl.GL_UNSIGNED_BYTE: gl.GLubyte
    # ...
}


def build_structure(fields):
    class _structure(Structure):
        _fields_ = [
            (name, gltypes[gltype] * size)
            for name, gltype, size in fields
        ]
    return _structure


class Vertices(LoggerMixin, metaclass=ABCMeta):

    _fields = [
        # The internal structure of each vertex
        # Should be a list of tuples (name, gltype, n_elements)
    ]

    def __init__(self, vao, data: List[Tuple[Tuple]], indices=None):
        self.vao = vao
        self.data = data

        self._structure = build_structure(self._fields)
        self.size = sizeof(self._structure)

        with vao:
            self.vertex_buffer = Buffer(data, self._structure)
            if indices:
                self.index_buffer = IndexBuffer(indices)
            else:
                self.index_buffer = IndexBuffer(range(len(self.data)))

        offset = 0
        for i, (name, type_, n_elements) in enumerate(self._fields):
            self.logger.debug("Attribute %d: %s", i, name)
            gl.glVertexArrayVertexBuffer(vao.name,
                                         i,  # binding index
                                         self.vertex_buffer.name,  # data storage
                                         offset,
                                         self.size)  # stride
            gl.glVertexArrayAttribFormat(vao.name,
                                         i,  # attr location
                                         n_elements,  # number of components per vertex e.g. 4 for vec4
                                         type_,  # type of values
                                         gl.GL_FALSE,  # normalized to 0..1?
                                         0)  # stride (0 means automatic)
            gl.glVertexArrayAttribBinding(vao.name,
                                          i,  # attrib location
                                          i)  # binding index
            offset += sizeof(gltypes[type_]) * n_elements
            gl.glEnableVertexArrayAttrib(vao.name, i)  # enable the attribute

        self.length = len(data)
        self.logger.debug("Length: %d, size: %d", self.length, self.size)

    @property
    def indexed(self):
        return bool(self.index_buffer)

    def draw(self, mode=gl.GL_TRIANGLES, indices=None):
        if indices:
            with indices:
                gl.glDrawElements(mode, len(indices), gl.GL_UNSIGNED_INT, 0)
        else:
            with self.index_buffer:
                gl.glDrawElements(mode, self.length, gl.GL_UNSIGNED_INT, 0)


class SimpleVertices(Vertices):

    _fields = [
        ('position', gl.GL_FLOAT, 3),
    ]


class ObjVertices(Vertices):

    """Vertices for storing OBJ (-like) data."""

    _fields = [
        ('position', gl.GL_FLOAT, 3),
        ('color', gl.GL_FLOAT, 3),
        ('normal', gl.GL_FLOAT, 3),
        ('texture', gl.GL_FLOAT, 3)
    ]
