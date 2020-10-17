from ctypes import byref, c_uint
from pyglet import gl
from typing import Dict, Tuple

from .texture import Texture, DepthTexture
from .glutil import GLTYPE_TO_CTYPE


black = (gl.GLfloat * 4)(0, 0, 0, 1)
white = (gl.GLfloat * 4)(1, 1, 1, 1)


class FrameBuffer:

    """
    Offscreen render buffer, e.g. for deferred rendering.
    Sometimes called a "G-buffer" (or geometry buffer) since it encodes
    geometry and material information per pixel. It can contain separate textures
    e.g. for color and normal, bound to different units so that they can
    all be used from shaders at the same time.

    Requires a size and a mapping of names to textures. The textures will be
    the "channels" of the framebuffer. They should probably have the same size
    as the framebuffer or there will be trouble. Also they must use different
    units.
    """

    def __init__(self, size: Tuple[int, int], textures: Dict[str, Texture],
                 depth_unit: int=None, autoclear: bool=False, set_viewport: bool=True):

        self.name = gl.GLuint()
        self.size = w, h = size
        self.autoclear = autoclear
        self.set_viewport = set_viewport

        gl.glCreateFramebuffers(1, byref(self.name))
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.name)

        # Create textures that we can use to read the results.
        self.textures = {}
        draw_attachments = []
        max_unit = 0
        for name, texture in textures.items():
            self.textures[name] = texture
            attachment = gl.GL_COLOR_ATTACHMENT0 + texture.unit
            gl.glFramebufferTexture(gl.GL_FRAMEBUFFER, attachment, texture.name, 0)
            draw_attachments.append(attachment)
            max_unit = max(max_unit, texture.unit)

        # Setup a depth buffer (presumably we always want that)
        depth_unit = depth_unit if depth_unit is not None else max_unit + 1
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
        if self.set_viewport:
            gl.glViewport(0, 0, *self.size)

    def __exit__(self, exc_type, exc_val, exc_tb):
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def __getitem__(self, texture_name: str):
        "Let textures be accessed as items, by name."
        return self.textures[texture_name]

    def clear(self):
        for index in range(len(self.textures)):
            gl.glClearBufferfv(gl.GL_COLOR, index, black)
        gl.glClearBufferfv(gl.GL_DEPTH, 0, white)

    def delete(self):
        gl.glDeleteFramebuffers(1, (c_uint*1)(self.name))
        
    def read_pixel(self, name: str, x: int, y: int, gl_type=gl.GL_FLOAT, gl_format=gl.GL_RGBA):
        """
        This is probably inefficient, but a useful way to find e.g. the scene position
        under the mouse cursor.
        """
        c_type = GLTYPE_TO_CTYPE[gl_type]
        texture = self.textures[name]
        position_value = (c_type * 4)()
        with self:
            gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0 + texture.unit)
            gl.glReadPixels(x, y, 1, 1, gl_format, gl_type, byref(position_value))
        return list(position_value)

    def __repr__(self):
        return f"Framebuffer(name={self.name}, size={self.size})"
    
