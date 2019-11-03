from ctypes import byref

from pyglet import gl

from .vertex import Vertices


class VertexArrayObject:

    """
    A vertex array object (VAO) is a kind of context object for a bunch of
    vertex buffers and related settings.
    """

    def __init__(self):
        self.name = gl.GLuint()
        gl.glCreateVertexArrays(1, byref(self.name))

    def __enter__(self):
        gl.glBindVertexArray(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindVertexArray(0)

    def create_vertices(self, data):
        "Just a convenience."
        return Vertices(self, data)
