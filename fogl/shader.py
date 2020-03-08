from abc import ABCMeta
from ctypes import cast, pointer, byref, create_string_buffer, POINTER, c_char
import io

from pyglet import gl

from .util import LoggerMixin


class Shader(LoggerMixin, metaclass=ABCMeta):

    """
    A light wrapper for GL shaders. Loads GLSL code from disk and compiles it.
    """

    def __init__(self, source_file: str=None, source: str=None):
        self.name = gl.glCreateShader(self.kind)
        if source_file:
            self.source = open(source_file, "rb").read()
        else:
            self.source = source
        src_buffer = create_string_buffer(self.source)
        buf_pointer = cast(pointer(pointer(src_buffer)), POINTER(POINTER(c_char)))
        gl.glShaderSource(self.name, 1, buf_pointer, None)
        gl.glCompileShader(self.name)
        success = gl.GLint(0)

        gl.glGetShaderiv(self.name, gl.GL_COMPILE_STATUS, byref(success))
        if not success.value:
            self._log_error()
            raise RuntimeError('Compiling of the shader failed.')

    def _log_error(self):
        log_length = gl.GLint(0)
        gl.glGetShaderiv(self.name, gl.GL_INFO_LOG_LENGTH, byref(log_length))

        log_buffer = create_string_buffer(log_length.value)
        gl.glGetShaderInfoLog(self.name, log_length.value, None, log_buffer)
        self.logger.error("Error compiling GLSL (type %s) shader!", self.kind)
        self.logger.error("---Shader---")
        self.logger.error(
            "\n".join(f"{i+1: 3d}: {line}"
                      for i, line in enumerate(self.source.decode("ascii").splitlines())))
        self.logger.error("---Message---")
        for line in log_buffer.value[:log_length.value].decode('ascii').splitlines():
            self.logger.error('GLSL: ' + line)
        self.logger.error("------")


class VertexShader(Shader):

    kind = gl.GL_VERTEX_SHADER


class GeometryShader(Shader):

    kind = gl.GL_GEOMETRY_SHADER


class FragmentShader(Shader):

    kind = gl.GL_FRAGMENT_SHADER


class Program(LoggerMixin):

    """
    A program consists of a set of Shaders. It should contain at least a
    vertex shader and a fragment shader. Geometry shader is optional.
    """

    def __init__(self, *shaders: Shader):
        self.name = gl.glCreateProgram()
        for shader in shaders:
            gl.glAttachShader(self.name, shader.name)

        gl.glLinkProgram(self.name)
        success = gl.GLint(0)
        gl.glGetProgramiv(self.name, gl.GL_LINK_STATUS, byref(success))

        if not success:
            log_length = gl.GLint(0)
            gl.glGetProgramiv(self.name, gl.GL_INFO_LOG_LENGTH, byref(log_length))
            log_buffer = create_string_buffer(log_length.value)
            gl.glGetProgramInfoLog(self.name, log_length.value, None, log_buffer)
            self.logger.error("Error linking program %s, error # %d", self.name, success.value)
            self.logger.error("---Message---")
            for line in log_buffer.value.decode("ascii").splitlines():
                self.logger.error("Program: " + line)
            self.logger.error("------")
            raise RuntimeError("Linking program failed.")

        # free resources
        for shader in shaders:
            gl.glDeleteShader(shader.name)

    def __enter__(self):
        gl.glUseProgram(self.name)

    def __exit__(self, *_):
        gl.glUseProgram(0)
