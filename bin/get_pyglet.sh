#!/bin/sh

git clone https://github.com/pyglet/pyglet.git
cd pyglet
# This script requires python 2.X
python2 tools/gengl.py glext_arb
# Drop "long" integer python2 syntax
sed -i 's/\([0-9]\+\)L/\1/g' pyglet/gl/glext_arb.py
# Apparent change in ctypes API between python2 and 3.X
sed -i 's/POINTER(c_void)/c_void_p/g' pyglet/gl/glext_arb.py
