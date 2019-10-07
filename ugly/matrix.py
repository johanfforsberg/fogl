"Helpful matrices for view calculations"

import math
from functools import lru_cache

from euclid3 import Matrix4


#@lru_cache(16)
def make_frustum(width, height, near=1, far=100):
    "view frustum matrix for the orthographic/isometric camera view"
    frust = Matrix4()
    frust[:] = (1/width, 0, 0, 0,
                0, 1/height, 0, 0,
                0, 0, -2/(far-near), 0,
                0, 0, -(far+near)/(far-near), 1)
    return frust


#@lru_cache(16)
def make_view_matrix(pos, rot, camera_distance, incidence, width, height, near, far):
    "Projection matrix (orthographic)"
    frust_mat = make_frustum(width, height, near, far)

    # View (camera position)
    # The setup can be visualized as a table where the scene
    # is placed, and the camera is initially at the origin, looking
    # downwards.
    # 1. Move the camera up (-z direction, note that axes are inverse since
    #    we're actually moving the scene, not the camera)
    # 2. Rotate it around the x-axis, until we are looking at the scene from
    #    the incidence angle.
    # 3. Turn it around the z-axis, to apply the scene's rotation.
    # 4. Translate the camera to the point it's supposed to be looking at.

    view_mat = (
        Matrix4
        .new_translate(0, 0, -camera_distance)  # 1
        .rotatex(-incidence)  # 2
        .rotatez(-rot)  # 3
        #.translate(0, 0, constants.PIXEL_ALIGNMENT_Z)  # this is a magic tweak to align pixels
        .translate(*pos)  # 4
    )

    return frust_mat * view_mat


@lru_cache(16)
def make_frustum_perspective(near=0.1, far=10, width=0.1, height=0.1):

    """View frustum for perspective corrected view, e.g. for
    point light shadow maps"""

    # Note: default is symmetric, 90 degree field of view

    # calculate a constant depth value offset over the frustum
    # http://canvas.projekti.info/ebooks/Mathematics%20for%203D%20Game%20Programming%20and%20Computer%20Graphics,%20Third%20Edition.pdf
    delta = 0.00  # manually tweaked
    pz = 1
    epsilon = 2 * far * near * delta / ((far + near) * pz * (pz + delta))

    frust = Matrix4.new(near/width, 0, 0, 0,
                        0, near/height, 0, 0,
                        0, 0, (1 + epsilon)*(-(far+near)/(far-near)), -1,
                        0, 0, -2*far*near/(far-near), 0)
    return frust


def make_view_matrix_persp(pos):
    frust = make_frustum_perspective()
    view_mat = (
        Matrix4
        .new_scale(1, 1, 1)
        .rotatez(math.pi)
        .rotatey(math.pi/2)
        .translate(*pos)
    )

    return frust * view_mat


@lru_cache(16)
def make_model_matrix(rotation=(0, 0, 0), translation=(0, 0, 0),
                      scale=(1., 1., 1.), window_size=(512, 512)):
    # Model
    # We may need to apply a transform to individual models.
    # w, h = window_size
    return (
        Matrix4()
        # here we rescale the Y axis to align with pixel size.
        # The idea is that we want the projected height of one block to
        # *exactly* correspond to 20 pixels, since that is the height
        # of the wall textures. Otherwise we'd get artefacts.
        # FIXME: window and texture size hard coded
        .scale(*scale)
        .scale(1, 1, constants.Z_SCALE)
        #.scale(1, 1, 1/math.sqrt(3))
        #.scale(1, 1, 1.017)
        .translate(*translation)
        .translate(0, 0, constants.BLOCK_CENTER_Z)
        .rotate_euler(*rotation)
    )

