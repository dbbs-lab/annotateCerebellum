"""
Utility functions for all applications.
"""
import nrrd
import numpy as np
from collections import OrderedDict

DEFAULT_HEADER = OrderedDict([('type', 'uint32'),
                              ('dimension', 3),
                              ('space dimension', 3),
                              ('sizes', np.array([528, 320, 456])),
                              ('space directions',
                               np.array([[25., 0., 0.],
                                         [0., 25., 0.],
                                         [0., 0., 25.]])),
                              ('endian', 'little'),
                              ('encoding', 'gzip'),
                              ('space origin', np.array([0., 0., 0.]))])


def load_nrrd_npy_file(filename):
    """
    Loads a volumetric nrrd file or a numpy file.

    :param str filename: path to the file to open.
    :return: volumetric array stored in file.
    :rtype: ndarray
    """
    if filename.endswith(".npy"):
        return np.load(filename)
    elif filename.endswith(".nrrd"):
        return nrrd.read(filename)[0]
    else:
        raise Exception("Extension not recognized, file could not be opened.")


def save_nrrd_npy_file(filename, data, header=None):
    """
    Save a volumetric array nrrd file or a numpy file.

    :param str filename: path to the file to save the data to.
    :param ndarray data: data to store in file
    :param dict header: Dictionary header for nrrd files
    """
    if filename.endswith(".npy"):
        np.save(filename, data)
    elif filename.endswith(".nrrd"):
        if header:
            nrrd.write(filename, data, header=header)
        else:
            nrrd.write(filename, data)
    else:
        raise Exception("Extension not recognized, file could not be opened.")


def find_group(image, position, id_reg):
    """
    Find all voxels labeled with the same id_reg id.

    :param np.ndarray image: Image 2D array.
    :param list position: Starting 2D position for exploration
    :param int id_reg: Id of the region group.
    :return: List of positions surrounding the starting position that match the id.
    :rtype: ndarray
    """
    explored = np.zeros(image.shape, dtype=bool)
    to_explore = [position]
    list_position = []
    while len(to_explore) > 0:
        current_pos = to_explore.pop()
        explored[current_pos[0], current_pos[1]] = True
        if image[current_pos[0], current_pos[1]] == id_reg:
            list_position.append(current_pos)
            for x, y in [[0, 1], [0, -1], [1, 0], [-1, 0]]:
                new_vox = [current_pos[0] + x, current_pos[1] + y]
                if not explored[new_vox[0], new_vox[1]] and new_vox not in to_explore:
                    to_explore.append(new_vox)
    return np.array(list_position)


def draw_2d_line(x0, y0, x1, y1):
    """
    Draws a 2D line between 2 points and returns intermediate positions.

    :return: list of pixel crossed by the line.
    :rtype: ndarray
    """
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    voxels = []
    while True:
        voxels.append([x0, y0])
        if abs(x0 - x1) < 1 and abs(y0 - y1) < 1:
            break
        e2 = 2 * error
        if e2 >= dy:
            if abs(x0 - x1) < 1:
                break
            error = error + dy
            x0 = x0 + sx
        if e2 <= dx:
            if abs(y0 - y1) < 1:
                break
            error = error + dx
            y0 = y0 + sy
    return np.unique(np.asarray(np.rint(np.array(voxels)), dtype=int), axis=0)
