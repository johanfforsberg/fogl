"""
Functionality for handling meshes, e.g. loading obj files.
"""

from .obj import parse_obj_file
from .vao import VertexArrayObject
from .vertex import ObjVertices


class Mesh:

    """
    A mesh is just a convenience for drawing vertices.
    """

    def __init__(self, data, texture=None, vertices_class=ObjVertices):
        self.data = data
        self.texture = texture
        self.vao = VertexArrayObject(vertices_class=vertices_class)
        self.vertices = self.vao.create_vertices(self.data)

    def __enter__(self):
        self.vao.__enter__()
        if self.texture:
            self.texture.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.texture:
            self.texture.__exit__(exc_type, exc_val, exc_tb)
        self.vao.__exit__(exc_type, exc_val, exc_tb)

    def draw(self, **kwargs):
        with self:
            self.vertices.draw(**kwargs)

    def __repr__(self):
        return f"Mesh(length={len(self.data)})"


class ObjMesh(Mesh):

    """
    Loads data from an OBJ (loghtwave) file into a mesh.
    """

    def __init__(self, path, texture):
        with open(path) as f:
            data = parse_obj_file(f)

        super().__init__(data, texture, vertices_class=ObjVertices)