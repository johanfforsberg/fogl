import logging
import math
from time import time

import pyglet
from pyglet import gl
from euclid3 import Matrix4

from ugly.framebuffer import FrameBuffer
from ugly.glutil import gl_matrix
from ugly.mesh import ObjMesh
from ugly.shader import Program, VertexShader, FragmentShader
from ugly.vao import VertexArrayObject


print(pyglet.__path__)


def try_except_log(f):
    "A decorator useful for debugging event callbacks whose exceptions get eaten by pyglet."
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            logging.exception(f"Exception caught in callback {f}.")
    return inner


class UglyWindow(pyglet.window.Window):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.view_program = Program(
            VertexShader("glsl/view_vertex.glsl"),
            FragmentShader("glsl/view_fragment.glsl")
        )
        self.copy_program = Program(
            VertexShader("glsl/copy_vertex.glsl"),
            FragmentShader("glsl/copy_fragment.glsl")
        )

        self.suzanne = ObjMesh("obj/suzanne.obj")

        self.vao = VertexArrayObject()

    def on_resize(self, width, height):
        self.size = width, height
        self.offscreen_buffer = FrameBuffer(self.size)
        return pyglet.event.EVENT_HANDLED  # Work around pyglet internals

    @try_except_log
    def on_draw(self):

        w, h = self.size
        aspect = h / w

        gl.glDisable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_CULL_FACE)

        # Render to an offscreen buffer
        with self.view_program, self.offscreen_buffer:

            # Setup our matrix
            near = 0.1
            far = 10
            width = 0.1
            height = 0.1 * aspect
            frustum = (Matrix4.new(
                near / width, 0, 0, 0,
                0, near / height, 0, 0,
                0, 0, -(far + near)/(far - near), -1,
                0, 0, -2 * far * near/(far - near), 0
            ))
            view_matrix = (Matrix4
                           .new_scale(1, 1, 1)
                           .translate(0, 0, -5)
                           .rotatex(-math.pi/2)
                           .rotatez(time()))
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE,
                                  gl_matrix(frustum * view_matrix))

            # Render a model
            self.offscreen_buffer.clear()
            self.suzanne.draw()

        # Now copy the offscreen buffer to the window's buffer
        with self.vao, self.copy_program:
            with self.offscreen_buffer.color_texture, \
                 self.offscreen_buffer.normal_texture:
                gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

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
