import logging
from itertools import chain
import math
from time import time
from pathlib import Path

import pyglet
from pyglet import gl
from euclid3 import Matrix4
import png

from ugly.framebuffer import FrameBuffer
from ugly.glutil import gl_matrix, load_png
from ugly.mesh import ObjMesh, Mesh
from ugly.shader import Program, VertexShader, FragmentShader
from ugly.texture import ImageTexture
from ugly.util import try_except_log
from ugly.vao import VertexArrayObject
from ugly.util import enabled, disabled


class UglyWindow(pyglet.window.Window):

    """
    Pyglet window subclass that draws an ugly scene every frame.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        local = Path(__file__).parent

        # Shader setup
        self.view_program = Program(
            VertexShader(local / "glsl/view_vertex.glsl"),
            FragmentShader(local / "glsl/view_fragment.glsl")
        )
        self.copy_program = Program(
            VertexShader(local / "glsl/copy_vertex.glsl"),
            FragmentShader(local / "glsl/copy_fragment.glsl")
        )

        size, image = load_png(str(local / "textures/face.png"))
        # print(list(chain.from_iterable(image)))
        texture = ImageTexture(image, size, unit=3)

        # Load vertex data from an OBJ file as a "mesh"
        self.suzanne = ObjMesh(local / "obj/suzanne.obj", texture=texture)

        # A simple plane
        self.plane = Mesh([

            # position        color          normal          texture coord
            ((1., 1., 0.),    (1., 1., 1.),  (0., 0., -1.),  (1., 1., 1.)),
            ((-1., 1., 0.),   (1., 1., 1.),  (0., 0., 1.),   (0., 1., 1.)),
            ((1., -1., 0.),   (1., 1., 1.),  (0., 0., -1.),  (1., 0., 1.)),
            ((-1., -1., 0.),  (1., 1., 1.),  (0., 0., -1.),  (0., 0., 1.)),

        ], texture=texture)

        self.vao = VertexArrayObject()

    def on_resize(self, width, height):
        self.size = width, height
        self.offscreen_buffer = FrameBuffer(self.size, autoclear=True)
        return pyglet.event.EVENT_HANDLED  # Work around pyglet internals

    @try_except_log
    def on_draw(self):

        w, h = self.size
        aspect = h / w

        # Render to an offscreen buffer
        with self.offscreen_buffer, self.view_program, \
             enabled(gl.GL_DEPTH_TEST), disabled(gl.GL_CULL_FACE):

            # Calculate our view matrix
            near = 0.1
            far = 15
            width = 0.05
            height = 0.05 * aspect
            frustum = (Matrix4.new(
                near / width, 0, 0, 0,
                0, near / height, 0, 0,
                0, 0, -(far + near)/(far - near), -1,
                0, 0, -2 * far * near/(far - near), 0
            ))
            view_matrix = (Matrix4
                           .new_scale(1, 1, 1)
                           .translate(0, 0, -8)
                           .rotatex(-math.pi/2)
                           .rotatez(time() * 10))
            # Set matrix uniform
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE,
                                  gl_matrix(frustum * view_matrix))

            # Render a model
            self.suzanne.draw()

            view_matrix = (Matrix4
                           .new_scale(1, 1, 1)
                           .translate(0, 0, -8))
            model_matrix = Matrix4.new_rotatex(-.5).rotatey(2.5).translate(0, 0, 2)
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE,
                                  gl_matrix(frustum * view_matrix * model_matrix))
            self.plane.draw(mode=gl.GL_TRIANGLE_STRIP)

        # Now copy the offscreen buffer to the window's buffer
        with self.vao, self.copy_program, disabled(gl.GL_CULL_FACE, gl.GL_DEPTH_TEST):
            # Bind some of the offscreen buffer's textures so the shader can read them.
            with self.offscreen_buffer.color_texture, \
                 self.offscreen_buffer.normal_texture:
                gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    config = pyglet.gl.Config(major_version=4,
                              minor_version=5,
                              double_buffer=True)

    DEBUG_GL = True
    pyglet.options['debug_gl'] = DEBUG_GL
    pyglet.options['debug_gl_trace'] = DEBUG_GL
    pyglet.options['debug_gl_trace_args'] = DEBUG_GL
    pyglet.options['debug_x11'] = DEBUG_GL

    w = UglyWindow(config=config)

    pyglet.clock.schedule_interval(lambda dt: None, 0.01)

    pyglet.app.run()
