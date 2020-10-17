"""
A simple animated scene that loads from OBJ, uses textures, and does deferred lighting with shadow map.
"""

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
    Pyglet window subclass that draws an scene every frame.
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
        plane_size = 3
        self.plane = Mesh([

            # position        color          normal          texture coord
            ((plane_size, plane_size, 0.),    (1., 1., 1.),  (0., 0., -1.),  (1., 1., 1.)),
            ((-plane_size, plane_size, 0.),   (1., 1., 1.),  (0., 0., -1.),  (0., 1., 1.)),
            ((plane_size, -plane_size, 0.),   (1., 1., 1.),  (0., 0., -1.),  (1., 0., 1.)),
            ((-plane_size, -plane_size, 0.),  (1., 1., 1.),  (0., 0., -1.),  (0., 0., 1.)),

        ], texture=texture)

        # A framebuffer for rendering the shadow light. It needs only a depth texture.
        self.shadow_size = 256, 256
        self.shadow_buffer = FrameBuffer(self.shadow_size, autoclear=True, depth_unit=3, set_viewport=True)
        
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
        self.offscreen_buffer = FrameBuffer(self.size, render_textures, autoclear=True, set_viewport=True)
        return pyglet.event.EVENT_HANDLED  # Work around pyglet internals

    @try_except_log
    def on_draw(self):

        # Model matrix we'll use to position the main model
        suzanne_model_matrix = (Matrix4
                        .new_identity()
                        .rotatex(-math.pi/2)
                        .rotatez(time()))  # Rotate over time
        plane_model_matrix = Matrix4.new_rotatey(math.pi).translate(0, 0, 2)
        
        # Render to an offscreen buffer
        with self.offscreen_buffer, self.view_program, \
                enabled(gl.GL_DEPTH_TEST), disabled(gl.GL_CULL_FACE):

            gl.glDepthMask(gl.GL_TRUE)
            
            w, h = self.size
            aspect = h / w
            
            # Calculate a view frustum; this is basically our camera.
            near = 5
            far = 15
            width = 2
            height = 2 * aspect
            frustum = (Matrix4.new(
                near / width, 0, 0, 0,
                0, near / height, 0, 0,
                0, 0, -(far + near)/(far - near), -1,
                0, 0, -2 * far * near/(far - near), 0
            ))

            # The view matrix positions the camera in the scene
            view_matrix = (Matrix4
                           .new_identity()
                           .translate(0, 0, -8))
            
            # Send the matrices to GL
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE,
                                  gl_matrix(frustum * view_matrix))
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE,
                                  gl_matrix(suzanne_model_matrix))            
            
            gl.glUniform4f(2, 0.3, 0.3, 1, 1)  # Set the "color" uniform to blue
            self.suzanne.draw()

            # We'll also draw a simple plane behind the main model
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE,
                                  gl_matrix(plane_model_matrix))
            gl.glUniform4f(2, 0.3, 1, 0.3, 1)  # Set the "color" uniform to green
            self.plane.draw(mode=gl.GL_TRIANGLE_STRIP)

        # Render shadow buffer
        # Basically the same scene as above, but to a different buffer and from a different view
        with self.shadow_buffer, self.view_program, enabled(gl.GL_DEPTH_TEST), disabled(gl.GL_CULL_FACE):
            gl.glDepthMask(gl.GL_TRUE)

            frustum = Matrix4.new_perspective(1, 1, 1, 12)
            view_matrix = (Matrix4
                           .new_identity()
                           .translate(0, 0, -4)
                           .rotatey(0.5)
                           .rotatex(0.3))
            light_pos = (view_matrix.inverse() * Point3(0, 0, 0))
            light_view_matrix = frustum * view_matrix
            gl.glUniformMatrix4fv(0, 1, gl.GL_FALSE,
                                  gl_matrix(frustum * view_matrix))
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE,
                                  gl_matrix(suzanne_model_matrix))            
            gl.glUniform4f(2, 0.9, 0.3, 0.4, 1)
            self.suzanne.draw()
            
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE,
                                  gl_matrix(plane_model_matrix))
            self.plane.draw(mode=gl.GL_TRIANGLE_STRIP)
            
        # Now draw the offscreen buffer to the window's buffer, combining it with the
        # lighting information to get a nice image.
        with self.vao, self.copy_program, disabled(gl.GL_CULL_FACE, gl.GL_DEPTH_TEST):
            gl.glUniform3f(0, *light_pos)
            gl.glUniformMatrix4fv(1, 1, gl.GL_FALSE, gl_matrix(light_view_matrix))
            # Bind some of the offscreen buffer's textures so the shader can read them.
            with self.offscreen_buffer["color"], self.offscreen_buffer["normal"], \
                    self.offscreen_buffer["position"], self.shadow_buffer["depth"]:
                gl.glViewport(0, 0, *self.size)
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
