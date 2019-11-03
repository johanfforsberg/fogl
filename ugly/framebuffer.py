from ctypes import byref
from pyglet import gl

from .texture import Texture, NormalTexture, DepthTexture


black = (gl.GLfloat * 4)(0, 0, 0, 1)
white = (gl.GLfloat * 4)(1, 1, 1, 1)


class FrameBuffer:

    """
    Offscreen render buffer, e.g. for deferred rendering.
    Sometimes called a "G-buffer" (or geometry buffer) since it encodes
    geometry and material information per pixel. It has separate textures
    for color, normal and position, bound to different units for simultaneous
    use in shaders.
    """

    def __init__(self, size, depth_unit=4, autoclear=False):
        self.name = gl.GLuint()
        self.size = w, h = size
        self.autoclear = autoclear

        gl.glCreateFramebuffers(1, byref(self.name))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.name)

        self.color_texture = Texture(self.size, unit=0)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, self.color_texture.name, 0)

        self.normal_texture = NormalTexture(self.size, unit=1)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT1, self.normal_texture.name, 0)

        self.position_texture = NormalTexture(self.size, unit=2)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT2, self.position_texture.name, 0)

        self.depth_texture = DepthTexture(self.size, unit=depth_unit)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, self.depth_texture.name, 0)

        self.draw_buffers = (gl.GLenum * 3)(
            gl.GL_COLOR_ATTACHMENT0,
            gl.GL_COLOR_ATTACHMENT1,
            gl.GL_COLOR_ATTACHMENT2
        )
        gl.glDrawBuffers(len(self.draw_buffers), self.draw_buffers)

        assert (gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) ==
                gl.GL_FRAMEBUFFER_COMPLETE), "Could not setup framebuffer!"

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def __enter__(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.name)
        if self.autoclear:
            self.clear()

    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def clear(self):
        gl.glClearBufferfv(gl.GL_COLOR, 0, black)
        gl.glClearBufferfv(gl.GL_COLOR, 1, black)
        gl.glClearBufferfv(gl.GL_COLOR, 2, black)
        gl.glClearBufferfv(gl.GL_DEPTH, 0, white)

    def read_pixel(self, x, y):
        """
        This is probably inefficient, but a useful way to find e.g. the scene position
        under the mouse cursor.
        """
        with self:
            position_value = (gl.GLfloat * 4)()
            gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT2)
            gl.glReadPixels(x, y, 1, 1, gl.GL_RGBA, gl.GL_FLOAT, byref(position_value))
        return list(position_value)
