from setuptools import setup

setup(
    name='fogl',
    version='0.1',
    description='Some OpenGL wrappers',
    author='Johan Forsberg',
    author_email='johan@slentrian.org',
    packages=['fogl'],
    # TODO Whenever pyglet 2.0 is released, switch to the PyPI package
    install_requires=['pyglet@git+https://github.com/pyglet/pyglet@v2.0.dev7']
)
