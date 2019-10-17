import logging


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
