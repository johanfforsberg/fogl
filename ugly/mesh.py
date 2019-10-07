"""
Functionality for handling meshes, e.g. loading obj files, transforming them and
stitching them together into level chunks.
"""

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import partial, lru_cache
from itertools import chain
from math import pi
from random import seed, randint
from traceback import format_exc

from euclid3 import Matrix4, Vector3

from .buffer import IndexBuffer
from .obj import parse_obj_file
from .util import LoggerMixin
from .glutil import immediately
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

    def transformed(self, **kwargs):
        return transform_mesh(self.data, **kwargs)

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
        # with resources.open_text(obj, path) as f:
        #     data = parse_obj_file(f)
        with open(path) as f:
            data = parse_obj_file(f)
        super().__init__(data, texture)


class ChunkMesh(LoggerMixin, Mesh):

    """
    Handles the mesh for a single chunk (NxNxN positions)
    """

    direction_angles = {
        "n": 0,
        "nw": pi/4,
        "w": pi/2,
        "sw": 3*pi/4,
        "s": pi,
        "se": 5*pi/4,
        "e": 3*pi/2,
        "ne": 7*pi/4
    }

    WALL_DIRECTIONS = "nesw"

    CORNER_WALL_DIRECTIONS = "ne", "nw", "se", "sw"

    def __init__(self, desc, meshes, texture, materials):
        self.vao = VertexArrayObject()
        self.desc = desc
        self.meshes = meshes
        self.texture = texture
        self.materials = materials
        self.data = []
        self.size = 0
        self.wall_map = {}
        self.build()
        self.room_map = self._make_room_walls()

    def _build_part(self, pos, direction, material_id=None, texture=None, info=(0, 0, 0), obj=None, rotation=None):
        print("build_part", info)
        if direction == "d":
            mesh = self.meshes["floor"].data
            z_rotation = get_floor_rotation(*pos)
            # TODO The index is intended mainly for mouse click/hover info per pixel
            # It is not nailed down yet, but for now:
            # 1st digit: "type"; 0 means nothing, 1 is floor, 2 is north wall, etc.
            # 2nd digit: no meaning yet
            # 3rd digit: no meaning yet
            #index = 1, 0, 0
        elif direction in self.WALL_DIRECTIONS:
            mesh = self.meshes["wall"].data
            z_rotation = self.direction_angles[direction] + pi/2
            #index = self.WALL_DIRECTIONS.index(direction) + 2, 0, 0
        # elif direction in self.DIAGONAL_WALL_DIRECTIONS:
        #     mesh = self.meshes["wall_diag"]
        #     z_rotation = self.direction_angles[direction] + pi/2
        #     #index = self.DIAGONAL_WALL_DIRECTIONS.index(direction) + 2, 0, 0
        elif direction == "c":
            z_rotation = rotation
            if obj:
                mesh = self.meshes[obj].data
            else:
                mesh = []
        else:
            raise RuntimeError(f"Failed to build part; unknown direction: {direction!r}")
        if material_id:
            material = self.materials[material_id]
        else:
            material = None
        self.size += 1
        return transform_mesh(mesh,
                              translate=pos,
                              rotate_z=z_rotation,
                              color=tuple(material["color"]) if material else (1, 1, 1),
                              texture=self.texture.get_texture_coords(material["texture_handle"]) if material else None,
                              info=tuple(info))

    def _build_block(self, pos, block_data):
        return [(pos, direction, list(self._build_part(pos, direction, **part_data)))
                for direction, part_data in block_data["walls"].items()]

    def build(self):
        try:
            data = list(chain.from_iterable(self._build_block(pos, block_data)
                                            for pos, block_data in self.desc.items()))
        except Exception as e:
            self.logger.error("Error building chunk: %s", format_exc())
            raise
        _, _, mesh_data = zip(*data)
        self.data = list(chain.from_iterable(mesh_data))
        self.vertices = self.vao.create_vertices(self.data)
        i = 0
        for pos, direction, mesh in data:
            i2 = i + len(mesh)
            self.wall_map[pos, direction] = (i, i2)
            i = i2
        print("wall_map", self.wall_map)

    def _make_room_walls(self):
        room_map = defaultdict(set)
        for (pos, direction), indices in self.wall_map.items():
            data = self.desc.get(pos)
            room = data["room"]
            if direction in ("d", "c"):
                room_map[room, "d"].add(indices)
            else:
                delta = constants.WALL_DELTAS[direction]
                neigh_pos = get_neighbor(pos, *delta)
                neigh_data = self.desc.get(neigh_pos)
                opposing_direction = constants.WALL_OPPOSING[direction]
                room_map[(room, direction)].add(indices)
                if neigh_data and opposing_direction in neigh_data["walls"]:
                    # This is the other side of the wall
                    room_map[(neigh_data["room"], opposing_direction)].add(indices)
        return room_map

    @lru_cache(16)
    def get_indices_excluding(self, exclude=()):
        indices = []
        excluded_ranges = set()
        # First go through the walls and check which ranges need exclusion
        # This is needed because most walls are stored twice in the room map
        # since they are "part" of two adjacent rooms. Probably storing this in
        # a smarter way could avoid this step...
        for room_dir, index_ranges in self.room_map.items():
            if room_dir in exclude:
                excluded_ranges.update(index_ranges)
        # Then, go through the mesh again and find what indices need skipping
        # to avoid drawing the excluded walls.
        for room_dir, index_ranges in self.room_map.items():
            for irange in index_ranges:
                if irange not in excluded_ranges:
                    indices.extend(range(*irange))
        return IndexBuffer(indices)

    @lru_cache(16)
    def get_indices_including(self, include=()):
        indices = []
        included_ranges = set()
        for room_dir, index_ranges in self.room_map.items():
            if room_dir in include:
                included_ranges.update(index_ranges)
        for irange in included_ranges:
            indices.extend(range(*irange))
        return IndexBuffer(indices)

    def __repr__(self):
        return f"ChunkMesh(size={self.size})"


# class ChunkMeshDict(LoggerMixin, dict):

#     "Not used ATM, intended for lazy loading of level data."

#     executor = ThreadPoolExecutor(max_workers=1)

#     def __init__(self, meshes, texture, materials):
#         super().__init__()
#         self.meshes = meshes
#         self.texture = texture
#         self.materials = materials
#         self.dirty_chunks = set()

#     def __setitem__(self, chunk, desc):
#         self.build_chunk(chunk, desc)

#     def build_chunk(self, chunk, desc):
#         self.logger.info("hej")
#         fut = self.executor.submit(ChunkMesh, desc, self.meshes, self.texture, self.materials)
#         fut.add_done_callback(partial(self._set, chunk))

#     @immediately
#     def _set(self, chunk, fut):
#         chunkmesh = fut.result()
#         super().__setitem__(chunk, chunkmesh)
#         self.dirty_chunks.add(chunk)
#         with chunkmesh.vao:
#             pass
#         self.logger.info("Stored %r: %r", chunk, chunkmesh)

#     def build_all(self):
#         for chunk, desc in self.items():
#             self.build_chunk(chunk, desc)


# def flatten(data):
#     return chain.from_iterable(chain.from_iterable(data))


def transform_texture(old, new=None):
    if new is None:
        return old
    x, y, z = old
    offset_x, offset_y, w, h = new
    return offset_x + x * w, offset_y + y * h, z


def transform_mesh(vertices, translate=(0, 0, 0), rotate_z=0, scale=(1, 1, 1),
                   color=None, texture=None, info=(0, 0, 0)):
    "Apply transformations to the given vertices."
    T = (Matrix4
         .new_rotatez(rotate_z)
         .scale(*scale)
         .scale(1.01, 1.01, 1.00))  # TODO Attempt to prevent "cracks" between adjacent walls
    N = T.inverse().transposed()
    return (
        (tuple(T * Vector3(*p[:3]) + Vector3(*translate)),
         color or c,
         tuple(N*Vector3(*n)),
         transform_texture(t, texture),
         info)
        for p, c, n, t in vertices
    )


@lru_cache()
def get_floor_rotation(x, y, z):
    """return a 'random' looking rotation in increments of pi/2, which is,
    and this is the point, *always the same* for a given (x, y, z).
    """
    p1 = 73856093
    p2 = 19349563
    p3 = 83492791
    seed(x * p1 + y * p2 + z * p3)
    return randint(0, 3) * pi/2


FLOOR_SQUARE = (
    ((-.5, -.5, -.5), (1, 1, 1), (0, 0, 1), (0, 0, 0)),
    ((.5, -.5, -.5), (1, 1, 1), (0, 0, 1), (1, 0, 0)),
    ((.5, .5, -.5), (1, 1, 1), (0, 0, 1), (1, 1, 0)),

    ((-.5, -.5, -.5), (1, 1, 1), (0, 0, 1), (0, 0, 0)),
    ((.5, .5, -.5), (1, 1, 1), (0, 0, 1), (1, 1, 0)),
    ((-.5, .5, -.5), (1, 1, 1), (0, 0, 1), (0, 1, 0))
)


@lru_cache(16)
def make_movement_grid(movements, maxcost, texture=None, texture_offset=(0, 0)):
    ox, oy = texture_offset
    return Mesh(list(chain.from_iterable(
        transform_mesh(FLOOR_SQUARE,
                       translate=pos,
                       texture=(ox/128, oy/128, 24/128, 24/128),
                       color=(1, 1, 0),
                       info=(1, cost/maxcost if maxcost > 0 else 1, 0))
        for pos, cost in movements
    )), texture)


@lru_cache(16)
def make_movement_outline(movements, maxcost, texture, texture_offset=(0, 0)):
    ox, oy = texture_offset
    return Mesh(list(chain.from_iterable(
        transform_mesh(FLOOR_SQUARE,
                       translate=pos,
                       texture=(ox, oy, (ox + 24)/128, (oy + 24)/128),
                       color=(1, 1, 0),
                       info=(1, cost/maxcost if maxcost > 0 else 1, 0))
        for pos, cost in movements
    )), texture)
