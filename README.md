Fogl
====

Fogl is a collection of utility wrappers around pyglet's raw OpenGL layer. 

It's purpose is to make GL programming more convenient, mostly by eliminating "boiler plate" code and helping with tracking state. Fogl tries to do as little as possible while still providing some useful abstractions. It's basically a bunch of classes that encapsulate some of the more annoying aspects of GL such as shaders and buffers. They are intended to be easy to subclass and modify. Where it makes sense, they work as context managers that keep track of state changes. There are also a few utilities included, e.g. for loading simple OBJ files. The GLSL programming and handling of uniforms etc is left up to you, as well as all the math.

Fogl is *not*, nor does it want to be, any of these things:

* A complete 3D framework that lets you get by without ever seeing the OpenGL API
* An opinionated library that helps you (or forces you to) structure your entire codebase.
* Really much of a stand alone library; one reasonable way to use it might be to incorporate the parts you like into your own code and customize it as needed. Or subclass the existing classes for your needs.

It does not attempt to cover the entire OpenGL API and every possible use case. Instead it does pretty much only what I need, in the way I like, and tries not to get in the way. Hopefully it's pretty easy to extend, though.

The dependency on pyglet does not mean that you necessarily have to build your entire application around pyglet. Fogl only uses the GL wrapper part of pyglet and should work with any other library that can coexist with pyglet, e.g. glfw.

Disclaimer: I'm not an OpenGL expert. Fogl is simply the result of numerous rewrites while trying to get some game code to make sense. Finally I broke it out into a separate package, to be able to use it in several projects. It works for what I'm doing but I'd be happy if it turned out to be useful to anyone else. If you find bugs or have any ideas about improvements feel free to file issues or pull requests. 


Usage
=====

The easiest way to see how to use Fogl is by taking a look at the example in `examples/example.py`, a simple application that opens a window and draws a spinning OBJ model loaded from file. It shows the GL settings you'll probably need to get fogl working, and how to setup and use shaders and do offscreen rendering. It relies on the `euclid3` library for calculating the view matrix.

Once we've created the offscreen buffer, we can use it simply by wrapping our GL draw calls with the buffer object as a context manager. The same goes for shader programs. The neat thing about this is that it becomes pretty easy to see in the code where the usage of these things begins and ends, and the most important setup and cleanup is handled behind the scenes.

There are also some convenient context managers ("enabled" and "disabled") for handling boolean GL flags. You can of course handle these yourself if you prefer, Fogl won't touch any of them unless you tell it to.

Drawing a mesh is simply done by calling the "draw" method on it.


Prerequisites
=============

Fogl requires at least python 3.6.

Fogl currently assumes you're able to run at least OpenGL 4.5. This is mostly because of my laziness; fogl was written with the help of the (excellent) "OpenGL Superbible", 7th ed. which relies on modern GL idioms. It may mean it won't work on older hardware.

Note that at the time of writing only the in-development 2.0 version of pyglet is supported (due to usage of more recent OpenGL features). 

In a clone of this repo:

```shell
$ python3 -m venv env 
$ env/bin/pip install -e .
```

To run the example included, you also need to install some additional libraries:

``` shell
$ env/bin/pip install euclid3 pypng imgui
$ env/bin/python examples/example.py
```
