from contextlib import contextmanager
from itertools import chain
import logging
from time import time

import png
import pyglet
from pyglet import gl


class LoggerMixin:

    @property
    def logger(self):
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger


def try_except_log(f):
    "A decorator useful for debugging event callbacks whose exceptions get eaten by pyglet."
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            logging.exception(f"Exception caught in callback {f}.")
    return inner


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
    Uses the pyglet clock to schedule calls.
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


@contextmanager
def enabled(*gl_flags):
    enabled = set()
    for f in gl_flags:
        if not gl.glIsEnabled(f):
            enabled.add(f)
            gl.glEnable(f)
    yield
    for f in enabled:
        gl.glDisable(f)


@contextmanager
def disabled(*gl_flags):
    disabled = set()
    for f in gl_flags:
        if gl.glIsEnabled(f):
            disabled.add(f)
            gl.glDisable(f)
    yield
    for f in disabled:
        gl.glEnable(f)


def load_png(filename):
    """
    An easy way to load a png file as a bunch of bytes,
    suitable for usage as a texture.
    """
    with open(filename, "rb") as f:
        reader = png.Reader(bytes=f.read())
        width, height, rows, info = reader.asRGBA()
        return (width, height), chain.from_iterable(rows)
