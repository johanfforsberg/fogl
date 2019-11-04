"""
Functionality related to textures.
"""

from ctypes import byref
from itertools import chain
from math import pi, sqrt

from euclid3 import Matrix4
from pyglet import gl

from .glutil import gl_matrix


class Texture:

    _type = gl.GL_RGBA8

    def __init__(self, size, unit=0):
        self.size = size
        self.unit = unit
        w, h = size
        self.name = gl.GLuint()
        gl.glCreateTextures(gl.GL_TEXTURE_2D, 1, byref(self.name))
        gl.glTextureStorage2D(self.name, 1, self._type, w, h)
        gl.glTextureParameteri(self.name,
                               gl.GL_TEXTURE_MIN_FILTER,
                               gl.GL_NEAREST)
        gl.glTextureParameteri(self.name,
                               gl.GL_TEXTURE_MAG_FILTER,
                               gl.GL_NEAREST)
        gl.glTextureParameteri(self.name,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_EDGE)
        gl.glTextureParameteri(self.name,
                               gl.GL_TEXTURE_WRAP_T,
                               gl.GL_CLAMP_TO_EDGE)

    def __enter__(self):
        gl.glActiveTexture(gl.GL_TEXTURE0 + self.unit)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glActiveTexture(gl.GL_TEXTURE0)

    def clear(self):
        gl.glClearTexImage(self.name, 0, gl.GL_RGBA, gl.GL_FLOAT, None)


class ByteTexture(Texture):

    _type = gl.GL_R8

    def clear(self):
        gl.glClearTexImage(self.name, 0, gl.GL_RED, gl.GL_UNSIGNED_BYTE, None)


class NormalTexture(Texture):

    _type = gl.GL_RGBA16F


class DepthTexture(Texture):

    _type = gl.GL_DEPTH_COMPONENT32F

    def clear(self):
        gl.glClearTexImage(self.name, 0, gl.GL_DEPTH, gl.GL_FLOAT, None)  # Correct?


class ImageTexture:

    def __init__(self, image, size, unit=0, atlas=None):
        self.image = image
        self.size = size
        self.unit = unit
        self.atlas = atlas
        self._setup()

    def _setup(self):
        self.name = gl.GLuint()
        gl.glCreateTextures(gl.GL_TEXTURE_2D, 1, byref(self.name))
        w, h = self.size
        gl.glTextureStorage2D(self.name, 1, gl.GL_RGBA8, w, h)
        gl.glTextureSubImage2D(
            self.name,
            0,  # level
            0, 0,  # offset
            w, h,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            (gl.GLchar * (4 * w * h))(*self.image)
        )
        gl.glTextureParameteri(self.name,
                               gl.GL_TEXTURE_MAG_FILTER,
                               gl.GL_NEAREST)
        gl.glTextureParameteri(self.name,
                               gl.GL_TEXTURE_MIN_FILTER,
                               gl.GL_NEAREST)

    def get_texture_coords(self, key):
        "Look up the given name in the texture atlas and return its UV coords"
        return self.image_coords_to_texture_coords(self.atlas[key])

    def image_coords_to_texture_coords(self, img_coords):
        iw, ih = self.size
        x, y, w, h = img_coords
        return x/iw, y/ih, w/iw-2, h/ih-2

    def __getitem__(self, key):
        "Return raw texture atlas coords"
        return self.atlas[key]

    def __enter__(self):
        gl.glActiveTexture(gl.GL_TEXTURE0 + self.unit)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glActiveTexture(gl.GL_TEXTURE0)


class CubeMap:

    # program = Program(
    #     VertexShader("copy_vert.glsl"),
    #     FragmentShader("shadow_frag.glsl"),
    # )

    def __init__(self, size):
        self.size = size
        self._setup()

    def _setup(self):
        self.name = gl.GLuint()

        gl.glCreateFramebuffers(1, byref(self.name))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.name)

        self.cubemap_texture = gl.GLuint()

        gl.glGenTextures(gl.GL_TEXTURE_CUBE_MAP, byref(self.name))
        gl.glBindTexture(gl.GL_TEXTURE_CUBE_MAP, self.cubemap_texture)

        w, h = self.size

        # initialize the texture (IMPORTANT!!!)
        for i in range(6):
            gl.glTexImage2D(gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0,
                            gl.GL_DEPTH_COMPONENT,
                            w, h, 0,
                            gl.GL_DEPTH_COMPONENT, gl.GL_FLOAT, 0)

        gl.glFramebufferTexture2D(gl.GL_DRAW_FRAMEBUFFER,
                                  gl.GL_DEPTH_ATTACHMENT,
                                  gl.GL_TEXTURE_CUBE_MAP_POSITIVE_X,
                                  self.cubemap_texture, 0)

        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_BASE_LEVEL, 0)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP, gl.GL_TEXTURE_MAX_LEVEL, 0)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP,
                           gl.GL_TEXTURE_WRAP_R,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_CUBE_MAP,
                           gl.GL_DEPTH_TEXTURE_MODE,
                           gl.GL_LUMINANCE)
        gl.glBindTexture(gl.GL_TEXTURE_CUBE_MAP, 0)

        status = gl.glCheckFramebufferStatus(gl.GL_DRAW_FRAMEBUFFER)
        assert status == gl.GL_FRAMEBUFFER_COMPLETE, f"Could not setup framebuffer! {status}"

    def render(self, position, chunk_meshes):

        gl.glViewport(0, 0, *self.size)
        gl.glDisable(gl.GL_BLEND)
        gl.glDisable(gl.GL_ALPHA_TEST)
        gl.glEnable(gl.GL_CULL_FACE)

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_LEQUAL)
        gl.glDepthMask(gl.GL_TRUE)

        x, y, z = position

        view_matrices = [
            Matrix4.new_scale(-1, -1, 1).rotatey(pi/2).translate(-x, -y, -z),  # +X
            Matrix4.new_scale(-1, -1, 1).rotatey(-pi/2).translate(-x, -y, -z),  # -X
            Matrix4.new_rotatex(-pi/2).translate(-x, -y, -z),  # +Y
            Matrix4.new_rotatex(pi/2).translate(-x, -y, -z),  # -Y
            Matrix4.new_scale(-1, -1, 1).rotatey(pi).translate(-x, -y, -z),  # +Z
            Matrix4.new_scale(-1, -1, 1).translate(-x, -y, -z)  # -Z
        ]

        model_matrix = Matrix4.new_scale(1, 1, constants.WALL_TEXTURE_HEIGHT / (constants.WALL_TEXTURE_WIDTH/sqrt(2) * (sqrt(3))))
        gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE, gl_matrix(model_matrix))
        with self.program, self.name:

            view_matrix = make_view_matrix_persp(position)
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE, gl_matrix(view_matrix))

            for chunk, mesh in chunk_meshes.items():
                mesh.draw()
