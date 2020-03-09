from ctypes import byref
from ctypes import c_uint

from pyglet import gl

from .vertex import Vertices


class VertexArrayObject:

    """
    A vertex array object (VAO) is a kind of context object for a bunch of
    vertex buffers and related settings.
    """

    def __init__(self, vertices_class=Vertices):
        self.name = gl.GLuint()
        self.vertices_class = vertices_class
        gl.glCreateVertexArrays(1, byref(self.name))

    def __enter__(self):
        gl.glBindVertexArray(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindVertexArray(0)

    def create_vertices(self, data):
        "Just a convenience."
        return self.vertices_class(self, data)

    def delete(self):
        gl.glDeleteVertexArrays(1, (c_uint*1)(self.name))
    
    def __del__(self):
        try:
            self.delete()
        except ImportError:
            pass
