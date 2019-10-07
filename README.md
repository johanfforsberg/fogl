Ugly
====

Ugly is a thin python wrapper around pyglet's OpenGL layer. 

It's purpose is to make GL programming more convenient, mostly by eliminating "boiler plate" code and helping with tracking state. Ugly tries to do as little as possible while still providing some useful abstractions. Ugly tries to make OpenGL programming feel more like python, without getting in the way of whatever it is you've got to do. It's really just a bunch of wrapper classes that encapsulate some of the more annoying GL stuff.

It's *not* any of these things:
* A complete 3D framework that lets you get by without ever seeing the OpenGL API
* An opinionated library that helps you (or forces you to) structure your code 
* Really a stand alone library at all; possibly the best way to use it is to incorporate it into your own code and customize it as needed.

Ugly currently does not care much about old versions of stuff; it assumes you're able to run at least OpenGL 4.5. This is mostly because of laziness; Ugly was written mostly using the OpenGL Superbible, 7th ed. which uses mainly 'modern' GL idioms.

The dependency on pyglet does not mean that you necessarily have to build your entire application using pyglet; Ugly only uses the GL wrapper part of pyglet and can be integrated with any other library that can coexist with pyglet. E.g. glfw works fine.



