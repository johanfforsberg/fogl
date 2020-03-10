import gc

import imgui
import pyglet
from pyglet import gl

from .framebuffer import FrameBuffer
from .texture import DepthTexture
from .imgui_pyglet import PygletRenderer


class DebugWindow(pyglet.window.Window):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, resizable=True)
        self.imgui_renderer = PygletRenderer(self)
        self.current_framebuffer = 0
    
    def on_draw(self):
        imgui.create_context()
        
        imgui.new_frame()
        
        imgui.begin("FrameBuffer", True)
        fbs = [o for o in gc.get_referrers(FrameBuffer) if isinstance(o, FrameBuffer)]
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        clicked, self.current_framebuffer = imgui.combo("FrameBuffer",
                                                        self.current_framebuffer,
                                                        [str(fb) for fb in fbs])

        fb = fbs[self.current_framebuffer]
        w, h = fb.size
        for name, tex in fb.textures.items():
            imgui.text(name)
            imgui.image(tex.name, 200, 200 * h/w)
        imgui.end()
            
        imgui.render()
        imgui.end_frame()
        
        data = imgui.get_draw_data()
        if data:
            self.imgui_renderer.render(imgui.get_draw_data())
        
