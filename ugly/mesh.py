"""
Functionality for handling meshes, e.g. loading obj files.
"""

from .obj import parse_obj_file
from .vao import VertexArrayObject


class MeshData:

    def __init__(self, data):
        self.data = data


class Mesh:

    def __init__(self, data, texture=None):
        self.data = data
        self.texture = texture
        self.vao = VertexArrayObject()
        self.vertices = self.vao.create_vertices(self.data)

    def __enter__(self):
        self.vao.__enter__()
        self.texture and self.texture.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.texture and self.texture.__exit__(exc_type, exc_val, exc_tb)
        self.vao.__exit__(exc_type, exc_val, exc_tb)

    def draw(self, **kwargs):
        if self.texture:
            with self.vao, self.texture:
                self.vertices.draw(**kwargs)
        else:
            with self.vao:
                self.vertices.draw(**kwargs)

    def __repr__(self):
        return f"Mesh(length={len(self.data)})"


class ObjMesh(Mesh):

    def __init__(self, path, texture=None):
        with open(path) as f:
            data = parse_obj_file(f)
        super().__init__(data, texture)
