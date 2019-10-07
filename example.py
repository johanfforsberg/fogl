import logging
import math
from time import time
from traceback import format_exc

import pyglet
from pyglet import gl
from euclid3 import Matrix4

from ugly.framebuffer import FrameBuffer
from ugly.glutil import gl_matrix
from ugly.texture import ImageTexture
from ugly.matrix import make_view_matrix_persp, make_frustum_perspective
from ugly.mesh import ObjMesh
from ugly.shader import Program, VertexShader, FragmentShader
from ugly.obj import parse_obj_file
from ugly.vao import VertexArrayObject


print(pyglet.__path__)


def try_except_log(f):
    "A decorator useful for debugging event callbacks whose exceptions get eaten by pyglet."
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            logging.error(format_exc())
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
        print(self.suzanne)

        self.vao = VertexArrayObject()

    def on_resize(self, width, height):
        self.size = width, height
        self.offscreen_buffer = FrameBuffer(self.size)
        return pyglet.event.EVENT_HANDLED  # Work around pyglet internals

    @try_except_log
    def on_draw(self):

        gl.glViewport(0, 0, *self.size)

        gl.glDisable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_CULL_FACE)

        w, h = self.size
        aspect = h / w

        # Render to an offscreen buffer
        with self.view_program, self.offscreen_buffer:
            gl.glClearBufferfv(gl.GL_COLOR, 0, (gl.GLfloat * 4)(1, 0, 0, 1))
            gl.glClearBufferfv(gl.GL_DEPTH, 0, (gl.GLfloat * 4)(1, 1, 1, 1))

            frust = make_frustum_perspective(height=0.1*aspect)
            view_matrix = (
                Matrix4
                .new_scale(1, 1, 1)
                .translate(0, 0, -5)
                .rotatey(-math.pi/2 + time())
                .rotatex(-math.pi/2)
            )
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE,
                                  gl_matrix(frust * view_matrix))
            self.suzanne.draw()

        # Now copy the offscreen buffer to the window's buffer
        with self.vao, self.copy_program:
            gl.glClearBufferfv(gl.GL_COLOR, 0, (gl.GLfloat * 4)(0, 0, 1, 1))
            with self.offscreen_buffer.color_texture:
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
