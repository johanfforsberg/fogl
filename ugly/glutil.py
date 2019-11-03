from ctypes import byref
from functools import lru_cache

from pyglet import gl


_gl_matrix = gl.GLfloat * 16


@lru_cache(256)
def gl_matrix(mat):
    return _gl_matrix(*mat)


def get_max_texture_size():
    max_texture_size = gl.GLint()
    gl.glGetIntegerv(gl.GL_MAX_TEXTURE_SIZE, byref(max_texture_size))
    return max_texture_size.value

