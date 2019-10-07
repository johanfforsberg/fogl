"""
Handling of GL vertex (attribute) data
"""


from ctypes import Structure, sizeof
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
}


def build_structure(fields):
    class _structure(Structure):
        _fields_ = [
            (name, gltypes[gltype] * size)
            for name, gltype, size in fields
        ]
    return _structure


class Vertices(LoggerMixin):

    _fields = [
        # (name, type, size)
        # TODO I think most of these could be lower precision, to save space.
        ('position', gl.GL_FLOAT, 3),
        ('color', gl.GL_FLOAT, 3),
        ('normal', gl.GL_FLOAT, 3),
        ('texture', gl.GL_FLOAT, 3),
        ('info', gl.GL_FLOAT, 3),  # internal data
    ]

    _structure = build_structure(_fields)

    def __init__(self, vao, data):
        self.vao = vao
        self.data = data
        with vao:
            self.vertex_buffer = Buffer(data, self._structure)
            self.index_buffer = IndexBuffer(range(len(self.data)))
        self.size = sizeof(self._structure)

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
        # TODO make this some kind of settings?
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_DEPTH_TEST)
        if indices:
            with indices:
                gl.glDrawElements(mode, len(indices), gl.GL_UNSIGNED_INT, 0)
        else:
            with self.index_buffer:
                gl.glDrawElements(mode, self.length, gl.GL_UNSIGNED_INT, 0)
            # gl.glDrawArrays(mode, 0, self.length)
