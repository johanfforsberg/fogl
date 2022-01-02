from ctypes import byref, create_string_buffer
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


GLTYPE_TO_CTYPE = {
    gl.GL_FLOAT: gl.GLfloat,
    gl.GL_BYTE: gl.GLbyte,
    gl.GL_UNSIGNED_BYTE: gl.GLubyte,
    gl.GL_INT: gl.GLint
}


def get_error_log(maxcount=10, bufsize=1000):
    """
    Reads whatever is currently in the error GL log.
    Note that this requires the GL context to have debugging enabled. In pyglet, this
    can be done by supplying a gl.Config object with the "debug" member set to True.
    """
    enum_array = gl.GLenum * maxcount
    sources = enum_array()
    types = enum_array()
    ids = enum_array()
    severities = enum_array()
    lengths = (gl.GLsizei * maxcount)()
    log_buffer = create_string_buffer(bufsize)
    count = gl.glGetDebugMessageLog(maxcount, bufsize, sources, types, ids, severities, lengths, log_buffer)
    return [log_buffer[:lengths[i]].decode('ascii') for i in range(count)]
