import nrrd
import numpy as np
from collections import OrderedDict

DEFAULT_HEADER = OrderedDict([('type', 'uint32'),
             ('dimension', 3),
             ('space dimension', 3),
             ('sizes', np.array([528, 320, 456])),
             ('space directions',
              np.array([[25.,  0.,  0.],
                     [ 0., 25.,  0.],
                     [ 0.,  0., 25.]])),
             ('endian', 'little'),
             ('encoding', 'gzip'),
             ('space origin', np.array([0., 0., 0.]))])


def load_nrrd_npy_file(filename):
    """
    Loads a volumetric nrrd file or a numpy file.
    :param filename: path to the file to open.
    :return: volumetric array stored in file.
    :rtype: np.ndarray
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
    :param filename: path to the file to save the data to.
    :param data: np.ndarray data to store in file
    :param header: Dictionary header for nrrd files
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