"""
Very simple Wavefront OBJ file loader.
Only supports the subset needed to load blender exported files,
and only cares about diffuse color materials.
"""

import logging
from typing import NamedTuple
import re
import os


logger = logging.getLogger("obj")


# Regexes to match the different types of lines
# (see https://en.wikipedia.org/wiki/Wavefront_.obj_file for reference)

INT = "-?\d+"
FLOAT = "-?\d+(?:\.\d+)?"
VERTEX = f"v +(?P<x>{FLOAT}) +(?P<y>{FLOAT}) +(?P<z>{FLOAT})"
          # f"(?: +(?P<r>{FLOAT}) +(?P<g>{FLOAT}) +(?P<b>{FLOAT}))?"
          # f"(?: +(?P<w>{FLOAT}))?")
TEXTURE = f"vt +(?P<x>{FLOAT}) +(?P<y>{FLOAT})( +(?P<w>{FLOAT}))?"
NORMAL = f"vn +(?P<x>{FLOAT}) +(?P<y>{FLOAT}) +(?P<z>{FLOAT})"
FACE = (f"f +(?P<v1>{INT})(?:/(?P<vt1>{INT})?(?:/(?P<vn1>{INT})?)?)?"
        f" +(?P<v2>{INT})(?:/(?P<vt2>{INT})?(?:/(?P<vn2>{INT})?)?)?"
        f" +(?P<v3>{INT})(?:/(?P<vt3>{INT})?(?:/(?P<vn3>{INT})?)?)?")


# some helpful classes to capture the obj file lines

class Vertex(NamedTuple):

    x: float
    y: float
    z: float

    # r: float = 1.0
    # g: float = 1.0
    # b: float = 1.0

    # w: float = 1.0


class Texture(NamedTuple):

    x: float
    y: float
    w: float = 1.0


class Normal(NamedTuple):

    x: float
    y: float
    z: float


class Face(NamedTuple):

    """Define (triangle) faces by referring to previously defined
    vertices/texture coords/normals by index"""

    # position
    v1: int
    v2: int
    v3: int

    # texture
    vt1: int = None
    vt2: int = None
    vt3: int = None

    # normal
    vn1: int = None
    vn2: int = None
    vn3: int = None


def make_tuple(tupleclass, match):

    "Convert a match result into the given kind of tuple"

    args = {
        field: (tupleclass._field_types[field](value)
                if value is not None
                else tupleclass._field_defaults[field])
        for field, value in match.groupdict().items()
    }
    return tupleclass(**args)


def parse_obj_line(line):
    if line.startswith("mtllib"):
        return ("mtllib", line[7:].strip())
    if line.startswith("usemtl"):
        return ("usemtl", line[7:].strip())
    if line.startswith("v "):
        return make_tuple(Vertex, re.match(VERTEX, line))
    if line.startswith("vt "):
        return make_tuple(Texture, re.match(TEXTURE, line))
    if line.startswith("vn "):
        return make_tuple(Normal, re.match(NORMAL, line))
    if line.startswith("f "):
        return make_tuple(Face, re.match(FACE, line))
    if line.startswith(("#", "o", "g", "usemtl")):
        return None


def parse_obj_file(f):
    vertices = []
    texture_coords = []
    normals = []
    result = []
    materials = {}

    def make_point(vertex, color, normal, texcoord):
        yield vertices[vertex-1]
        yield color
        if normal is None:
            yield (0, 0, 1)
        else:
            yield normals[normal-1]
        if texcoord is None:
            yield (0, 0, 0)
        else:
            yield texture_coords[texcoord-1]

    color = (1, 1, 1)

    for line in f:
        item = parse_obj_line(line)
        if item is None:
            continue
        if isinstance(item, Vertex):
            vertices.append(item)
        elif isinstance(item, Texture):
            texture_coords.append(item)
        elif isinstance(item, Normal):
            normals.append(item)
        elif isinstance(item, Face):
            result.append(tuple(make_point(item.v1, color, item.vn1, item.vt1)))
            result.append(tuple(make_point(item.v2, color, item.vn2, item.vt2)))
            result.append(tuple(make_point(item.v3, color, item.vn3, item.vt3)))
        elif isinstance(item, tuple):
            if item[0] == "mtllib":
                current_dir = os.getcwd()
                os.chdir(os.path.dirname(f.name))
                materials.update(parse_mtl_file(item[1]))
                os.chdir(current_dir)
            elif item[0] == "usemtl":
                color = materials[item[1]]

    return result


# Material file, referenced from obj

DIFFUSE = f"Kd +(?P<r>{FLOAT}) +(?P<g>{FLOAT}) +(?P<b>{FLOAT})"


class Diffuse(NamedTuple):

    r: float = 0.2
    g: float = 0.2
    b: float = 0.2


def parse_mtl_line(line):
    if line.startswith("newmtl"):
        return ("newmtl", line[7:].strip())
    if line.startswith("Kd "):
        return make_tuple(Diffuse, re.match(DIFFUSE, line))
    else:
        return None


def parse_mtl_file(filename):
    materials = {}
    with open(filename) as f:
        material = None
        for line in f:
            item = parse_mtl_line(line)
            if item is None:
                continue
            if isinstance(item, Diffuse):
                materials[material] = item
            elif isinstance(item, tuple):
                if item[0] == "newmtl":
                    material = item[1]
    return materials
