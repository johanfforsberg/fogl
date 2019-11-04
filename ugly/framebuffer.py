from ctypes import byref
from pyglet import gl
from typing import Dict, Tuple

from .texture import Texture, DepthTexture


black = (gl.GLfloat * 4)(0, 0, 0, 1)
white = (gl.GLfloat * 4)(1, 1, 1, 1)


class FrameBuffer:

    """
    Offscreen render buffer, e.g. for deferred rendering.
    Sometimes called a "G-buffer" (or geometry buffer) since it encodes
    geometry and material information per pixel. It can contain separate textures
    e.g. for color and normal, bound to different units so that they can
    all be used from shaders at the same time.
    """

    def __init__(self, size: Tuple[int, int], textures: Dict[str, Texture],
                 depth_unit: int=None, autoclear: bool=False):

        self.name = gl.GLuint()
        self.size = w, h = size
        self.autoclear = autoclear

        gl.glCreateFramebuffers(1, byref(self.name))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.name)

        # Create textures that we can use to read the results.
        self.textures = {}
        draw_attachments = []
        for index, (name, texture) in enumerate(textures.items()):
            self.textures[name] = texture
            gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0 + index, texture.name, 0)
            draw_attachments.append(gl.GL_COLOR_ATTACHMENT0 + index)

        # Setup a depth buffer (presumably we always want that)
        depth_unit = depth_unit if depth_unit is not None else len(textures)
        self.textures["depth"] = depth_texture = DepthTexture(self.size, unit=depth_unit)
        gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, gl.GL_DEPTH_ATTACHMENT, depth_texture.name, 0)

        # Setup draw buffers and connect them to the textures.
        self.draw_buffers = (gl.GLenum * len(textures))(*draw_attachments)
        gl.glDrawBuffers(len(self.draw_buffers), self.draw_buffers)

        # Check that it all went smoothly
        assert (gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) ==
                gl.GL_FRAMEBUFFER_COMPLETE), "Could not setup framebuffer!"

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def __enter__(self):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.name)
        if self.autoclear:
            self.clear()

    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def __getitem__(self, texture_name):
        "Let textures be accessed as items, by name."
        return self.textures[texture_name]

    def clear(self):
        for index in range(len(self.textures)):
            gl.glClearBufferfv(gl.GL_COLOR, index, black)
        gl.glClearBufferfv(gl.GL_DEPTH, 0, white)

    def read_pixel(self, name, x, y):
        """
        This is probably inefficient, but a useful way to find e.g. the scene position
        under the mouse cursor.
        """
        unit = self.textures[name].unit
        with self:
            position_value = (gl.GLfloat * 4)()
            gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0 + unit)
            gl.glReadPixels(x, y, 1, 1, gl.GL_RGBA, gl.GL_FLOAT, byref(position_value))
        return list(position_value)
