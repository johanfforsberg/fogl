ugly
====

ugly is a collection of utility wrappers around pyglet's OpenGL layer. 

It's purpose is to make GL programming more convenient, mostly by eliminating "boiler plate" code and helping with tracking state. ugly tries to do as little as possible while still providing some useful abstractions. It's basically a bunch of classes that encapsulate some of the more annoying aspects of GL. They are intended to be easy to subclass and modify. Many of them work as context managers that keep track of state changes. There are also a few utilities included, e.g. for loading OBJ files.

ugly is not, nor does it want to be, any of these things:

* A complete 3D framework that lets you get by without ever seeing the OpenGL API
* An opinionated library that helps you (or forces you to) structure your code 
* Really much of a stand alone library at all; one reasonable way to use it might be to incorporate the parts you like into your own code and customize it as needed.

ugly currently assumes you're able to run at least OpenGL 4.5. This is mostly because of laziness; ugly was written with the help of the excellent "OpenGL Superbible", 7th ed. which relies on modern GL idioms. ugly also requires at least python 3.6.

Note: The dependency on pyglet does not mean that you necessarily have to build your entire application around pyglet. ugly only uses pyglet's GL wrapper and should work with any other library that can coexist with pyglet, e.g. glfw.

Disclaimer: I'm not an OpenGL expert. ugly is simply the result of numerous rewrites trying to get some game code to make sense. Finally I just broke it out into a separate package, to be able to use it in several projects. It works for what I'm doing and I'm hoping it can be useful to others. If you have any ideas about improvements feel free to file issues or pull requests.
