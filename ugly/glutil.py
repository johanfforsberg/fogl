from ctypes import byref
from functools import lru_cache
from itertools import chain

from pyglet import gl
import png


_gl_matrix = gl.GLfloat * 16


@lru_cache(256)
def gl_matrix(mat):
    return _gl_matrix(*mat)


def get_max_texture_size():
    max_texture_size = gl.GLint()
    gl.glGetIntegerv(gl.GL_MAX_TEXTURE_SIZE, byref(max_texture_size))
    return max_texture_size.value


def load_png(filename):
    """
    An easy way to load a png file as a bunch of bytes,
    suitable for usage as a texture.
    """
    with open(filename, "rb") as f:
        reader = png.Reader(bytes=f.read())
        width, height, rows, info = reader.asRGBA()
        return (width, height), chain.from_iterable(rows)
