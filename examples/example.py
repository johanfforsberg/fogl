import logging
import math
from time import time
from pathlib import Path

import pyglet
from pyglet import gl
from euclid3 import Matrix4, Point3

from fogl.debug import DebugWindow
from fogl.framebuffer import FrameBuffer
from fogl.glutil import gl_matrix
from fogl.mesh import ObjMesh, Mesh
from fogl.shader import Program, VertexShader, FragmentShader
from fogl.texture import ImageTexture, Texture, NormalTexture
from fogl.util import try_except_log, load_png
from fogl.vao import VertexArrayObject
from fogl.util import enabled, disabled


class FoglWindow(pyglet.window.Window):

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

        # Load a texture
        texture = ImageTexture(*load_png(local / "textures/plasma.png"), unit=3)

        # Load vertex data from an OBJ file as a "mesh"
        # OBJ file belongs to the Blender project.
        self.suzanne = ObjMesh(local / "obj/suzanne.obj", texture=texture)

        # A simple plane
        self.plane = Mesh([

            # position        color          normal          texture coord
            ((1., 1., 0.),    (1., 1., 1.),  (0., 0., -1.),  (1., 1., 1.)),
            ((-1., 1., 0.),   (1., 1., 1.),  (0., 0., -1.),  (0., 1., 1.)),
            ((1., -1., 0.),   (1., 1., 1.),  (0., 0., -1.),  (1., 0., 1.)),
            ((-1., -1., 0.),  (1., 1., 1.),  (0., 0., -1.),  (0., 0., 1.)),

        ], texture=texture)

        self.shadow_size = 256, 256
        shadow_textures = dict(
            # These will represent the different channels of the framebuffer,
            # that the shader can render to.
            color=Texture(self.shadow_size, unit=0),
            normal=NormalTexture(self.shadow_size, unit=1),
            position=NormalTexture(self.shadow_size, unit=2),
        )
        self.shadow_buffer = FrameBuffer(self.shadow_size, shadow_textures, autoclear=True)
        
        self.vao = VertexArrayObject()

    def on_resize(self, width, height):
        self.size = width, height
        # We need to recreate the offscreen buffer if the window size changes
        # This includes when the window is first created.
        render_textures = dict(
            # These will represent the different channels of the framebuffer,
            # that the shader can render to.
            color=Texture(self.size, unit=0),
            normal=NormalTexture(self.size, unit=1),
            position=NormalTexture(self.size, unit=2),
        )
        self.offscreen_buffer = FrameBuffer(self.size, render_textures, autoclear=True)
        return pyglet.event.EVENT_HANDLED  # Work around pyglet internals

    @try_except_log
    def on_draw(self):

        # Render shadow buffer
        with self.shadow_buffer, self.view_program, enabled(gl.GL_DEPTH_TEST), disabled(gl.GL_CULL_FACE):
            gl.glDepthMask(gl.GL_TRUE)

            w, h = self.shadow_size
            aspect = h / w
            
            near = 5
            far = 12
            width = 2
            height = 2 * aspect
            # frustum = (Matrix4.new(
            #     near / width, 0, 0, 0,
            #     0, near / height, 0, 0,
            #     0, 0, -(far + near)/(far - near), -1,
            #     0, 0, -2 * far * near/(far - near), 0
            # ))
            frustum = Matrix4.new_perspective(0.5, 1, 5, 10)
            view_matrix = (Matrix4
                           .new_identity()
                           .translate(0, 0, -8)
                           .rotatey(0.5)
                           .rotatex(0.3))
            shadow_view_matrix = frustum * view_matrix
            light_pos = (view_matrix.inverse() * Point3(0, 0, 0))
            model_matrix = (Matrix4
                            .new_identity()
                            .rotatex(-math.pi/2)
                            # .rotatey(-math.pi/5)
                            .rotatez(time()))  # Rotate over time
            print(light_pos)
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE,
                                  gl_matrix(frustum * view_matrix))
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE,
                                  gl_matrix(model_matrix))            
            gl.glUniform4f(2, 0.9, 0.3, 0.4, 1)
            gl.glCullFace(gl.GL_FRONT)
            self.suzanne.draw()

            # We'll also draw a plane which is stationary
            model_matrix = Matrix4.new_rotatex(-.5).rotatey(2.5).translate(0, 0, 2)
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE,
                                  gl_matrix(model_matrix))
            gl.glUniform4f(2, 0.3, 1, 0.3, 1)  # Set the "color" uniform to green
            self.plane.draw(mode=gl.GL_TRIANGLE_STRIP)
            gl.glCullFace(gl.GL_BACK)
            
        # Render to an offscreen buffer
        with self.offscreen_buffer, self.view_program, \
                enabled(gl.GL_DEPTH_TEST), disabled(gl.GL_CULL_FACE):

            w, h = self.size
            aspect = h / w
            
            near = 5
            far = 12
            width = 2
            height = 2 * aspect
            frustum = (Matrix4.new(
                near / width, 0, 0, 0,
                0, near / height, 0, 0,
                0, 0, -(far + near)/(far - near), -1,
                0, 0, -2 * far * near/(far - near), 0
            ))

            gl.glDepthMask(gl.GL_TRUE)
            
            # Calculate a view frustum; this is basically our camera.

            # First we'll draw our OBJ model
            view_matrix = (Matrix4
                           .new_identity()
                           .translate(0, 0, -8))
            model_matrix = (Matrix4
                            .new_identity()
                            .rotatex(-math.pi/2)
                            # .rotatey(-math.pi/5)
                            .rotatez(time()))  # Rotate over time
            # Send the matrix to GL
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE,
                                  gl_matrix(frustum * view_matrix))
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE,
                                  gl_matrix(model_matrix))            
            
            gl.glUniform4f(2, 0.3, 0.3, 1, 1)  # Set the "color" uniform to blue
            self.suzanne.draw()

            # We'll also draw a plane which is stationary
            model_matrix = Matrix4.new_rotatex(-.5).rotatey(2.5).translate(0, 0, 2)
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE,
                                  gl_matrix(model_matrix))
            gl.glUniform4f(2, 0.3, 1, 0.3, 1)  # Set the "color" uniform to green
            self.plane.draw(mode=gl.GL_TRIANGLE_STRIP)

        # Now copy the offscreen buffer to the window's buffer
        with self.vao, self.copy_program, disabled(gl.GL_CULL_FACE, gl.GL_DEPTH_TEST):
            # Bind some of the offscreen buffer's textures so the shader can read them.
            # with self.shadow_buffer["color"], self.shadow_buffer["normal"], \
            #          self.shadow_buffer["position"], self.shadow_buffer["depth"]:
            #    gl.glDrawArrays(gl.GL_TRIANGLES, 0, 6)
            gl.glUniform3f(0, *light_pos)
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE, gl_matrix(shadow_view_matrix))
            with self.offscreen_buffer["color"], self.offscreen_buffer["normal"], self.offscreen_buffer["position"], self.shadow_buffer["depth"]:
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

    w = FoglWindow(config=config, resizable=True)
    # DebugWindow()

    pyglet.clock.schedule_interval(lambda dt: None, 0.01)

    pyglet.app.run()
