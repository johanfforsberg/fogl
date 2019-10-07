"""
Offscreen render buffer, e.g. for deferred rendering.
"""

from ctypes import byref
from pyglet import gl

from .texture import Texture, NormalTexture, DepthTexture


class FrameBuffer:

    def __init__(self, size, depth_unit=4):
        self.name = gl.GLuint()
        self.size = w, h = size
        gl.glCreateFramebuffers(1, byref(self.name))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.name)

        self.color_texture = Texture(self.size, unit=0)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, self.color_texture.name, 0)

        self.normal_texture = NormalTexture(self.size, unit=1)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT1, self.normal_texture.name, 0)

        self.position_texture = NormalTexture(self.size, unit=2)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT2, self.position_texture.name, 0)

        self.info_texture = Texture(self.size, unit=3)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT3, self.info_texture.name, 0)

        self.depth_texture = DepthTexture(self.size, unit=depth_unit)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, self.depth_texture.name, 0)

        self.draw_buffers = (gl.GLenum * 4)(
            gl.GL_COLOR_ATTACHMENT0,
            gl.GL_COLOR_ATTACHMENT1,
            gl.GL_COLOR_ATTACHMENT2,
            gl.GL_COLOR_ATTACHMENT3
        )
        gl.glDrawBuffers(len(self.draw_buffers), self.draw_buffers)

        assert (gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) ==
                gl.GL_FRAMEBUFFER_COMPLETE), "Could not setup framebuffer!"

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def __enter__(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def read_pixel(self, x, y):
        with self:
            color_value = (gl.GLubyte * 4)()
            gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0)
            gl.glReadPixels(x, y, 1, 1, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, byref(color_value))
            position_value = (gl.GLfloat * 4)()
            gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT2)
            gl.glReadPixels(x, y, 1, 1, gl.GL_RGBA, gl.GL_FLOAT, byref(position_value))
            info_value = (gl.GLubyte * 4)()
            gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT3)
            gl.glReadPixels(x, y, 1, 1, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, byref(info_value))
        return list(position_value), list(info_value)
