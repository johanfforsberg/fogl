from ctypes import byref
from functools import lru_cache
from time import time

import pyglet


_gl_matrix = pyglet.gl.GLfloat * 16


@lru_cache(256)
def gl_matrix(mat):
    return _gl_matrix(*mat)


def get_max_texture_size():
    max_texture_size = pyglet.gl.GLint()
    pyglet.gl.glGetIntegerv(pyglet.gl.GL_MAX_TEXTURE_SIZE, byref(max_texture_size))
    return max_texture_size.value


def throttle(interval=0.1):
    """
    A decorator that ensures that the function is not run more often
    than the given interval, no matter how often it's called.
    Uses the pyglet clock to schedule calls.
    """
    scheduled_at = None

    def wrap(f):
        def inner(*args, **kwargs):
            nonlocal scheduled_at
            now = time()
            if scheduled_at and scheduled_at > now:
                return
            scheduled_at = now + interval

            pyglet.clock.schedule_once(lambda dt: f(*args, **kwargs), interval)
        return inner

    return wrap


def debounce(interval=0.1):
    """
    Decorator that causes the function to be delayed until such time that it has
    not been called for at least interval seconds. Useful for preventing a function from
    being run several times in rapid succession.
    """
    last_func = None

    def wrap(f):
        def inner(*args, **kwargs):
            nonlocal last_func
            if last_func:
                pyglet.clock.unschedule(last_func)
            last_func = lambda dt: f(*args, **kwargs)
            pyglet.clock.schedule_once(last_func, interval)
        return inner

    return wrap



immediately = throttle(interval=0)  # convenient for calling GL stuff from another thread

