"""
Model part of the application to visualize and modify cerebellar cortex annotation.
"""
import numpy as np

from annotate_cerebellum.utils import find_group

DICT_REG_NUMBERS = {
    "out": 0,
    "fib": 1,
    "prot": 2,
    "mol": 3,
    "gl": 4,
}

DICT_REG_COLORS = {
    "mol": (0, 1, 0),
    "gl": (1, 0, 0),
    "fib": (0, 0, 1),
    "out": (0, 0, 0),
    "prot": (1, 0, 1),
}


class AnnotationImage:
    """
    Class of the model of the user application to modify volumetric cerebellar annotations.
    Applies modification on the annotations.
    """

    def __init__(self, annotation, dict_reg_ids, nissl):
        """
        Initialize the annotation model class.

        :param ndarray annotation: Volumetric array of integers corresponding to brain region ids
        :param dict dict_reg_ids: Dictionary linking keys of DICT_REG_NUMBERS and DICT_REG_COLORS to
            their list brain region ids
        :param ndarray nissl: Volumetric array of float corresponding to nissl expression
        """
        self.annotation = annotation
        self.nissl = nissl
        if self.nissl.shape != self.annotation.shape:
            raise Exception("The annotation and nissl volumes must have the same shape.")
        self.dict_reg_ids = dict_reg_ids
        self.inv_dict_reg_ids = np.zeros(np.max(list(DICT_REG_NUMBERS.values())) + 1, dtype=int)
        self.inv_dict_reg_ids[DICT_REG_NUMBERS["mol"]] = self.dict_reg_ids["mol"][0]
        self.inv_dict_reg_ids[DICT_REG_NUMBERS["gl"]] = self.dict_reg_ids["gl"][0]
        self.inv_dict_reg_ids[DICT_REG_NUMBERS["fib"]] = self.dict_reg_ids["fib"][0]

        self.annCPY = np.zeros(annotation.shape, np.int8)
        self.annCPY[self.annotation > 0] = -1
        for key, value in DICT_REG_NUMBERS.items():
            self.annCPY[np.isin(self.annotation, self.dict_reg_ids[key])] = value
        self.backup = np.copy(self.annCPY)
        self.previous_state = np.copy(self.annCPY)

        filter_ = np.where(np.isin(self.annCPY, [DICT_REG_NUMBERS["mol"], DICT_REG_NUMBERS["gl"]]))
        self.idsX = [np.min(filter_[0]) - 1, np.max(filter_[0]) + 1]
        self.idsY = [max(0, np.min(filter_[1] - 80)),
                     min(int(annotation.shape[1]) - 1, np.max(filter_[1] + 80))]
        self.idsZ = [max(0, np.min(filter_[2] - 120)),
                     min(int(annotation.shape[2]) - 1, np.max(filter_[2] + 120))]
        self.idX = int(np.mean(filter_[0]))
        self.generate_image()

    def generate_image(self):
        """
        Generate a 2D RGB image which correspond to the current coronal slice.
        """
        slice_pos = np.s_[self.idX, self.idsY[0]:self.idsY[1] + 1, self.idsZ[0]:self.idsZ[1] + 1]
        self.picRGB = np.zeros((self.annCPY[slice_pos].shape[0],
                                self.annCPY[slice_pos].shape[1], 3), np.uint16)
        self.picRGB[:, :, 0] = self.picRGB[:, :, 1] = self.picRGB[:, :, 2] = np.uint16(
            255.0 * (self.nissl[slice_pos] / np.max(self.nissl[slice_pos])))

        self.nissl_img = np.copy(self.picRGB)

        for key, value in DICT_REG_NUMBERS.items():
            filter_ = np.where(self.annCPY[slice_pos] == value)
            self.picRGB[filter_[0], filter_[1], :] += np.uint16(77 * np.array(DICT_REG_COLORS[key]))
        self.picRGB[self.picRGB > 255] = 255
        self.picRGB = np.asarray(self.picRGB, dtype=np.uint8)

    def update_slice(self, voxels_to_update, key):
        """
        Change the value of the voxels listed in parameters in the annotations.

        :param ndarray voxels_to_update: list of voxels to update
        :param str key: Key of the DICT_REG_NUMBERS and DICT_REG_COLORS corresponding to the new
            value.
        """
        change = False
        for voxel in voxels_to_update:
            slice_pos = np.s_[self.idX, self.idsY[0] + voxel[0], self.idsZ[0] + voxel[1]]
            if 0 <= voxel[0] < self.picRGB.shape[0] and \
                    0 <= voxel[1] < self.picRGB.shape[1] and \
                    not self.annCPY[slice_pos] == DICT_REG_NUMBERS["prot"] and \
                    self.annCPY[slice_pos] != DICT_REG_NUMBERS[key]:
                if not change:
                    self.previous_state = np.copy(self.annCPY)
                    change = True
                self.annCPY[slice_pos] = DICT_REG_NUMBERS[key]
                self.picRGB[voxel[0], voxel[1]] = np.uint8(
                    np.minimum(self.nissl_img[voxel[0],
                                              voxel[1]] + 77 * np.array(DICT_REG_COLORS[key]), 255))

    def revert_slice(self):
        self.annCPY = np.copy(self.previous_state)
        self.generate_image()

    def revert_voxels(self, voxels_to_update):
        """
        Revert changes in the annotations at the location of the list of voxels in parameter.

        :param ndarray voxels_to_update: list of voxels to revert.
        """
        for voxel in voxels_to_update:
            slice_pos = np.s_[self.idX, self.idsY[0] + voxel[0], self.idsZ[0] + voxel[1]]
            if 0 <= voxel[0] < self.picRGB.shape[0] and \
                    0 <= voxel[1] < self.picRGB.shape[1] and \
                    not self.annCPY[slice_pos] == DICT_REG_NUMBERS["prot"]:
                self.annCPY[slice_pos] = self.backup[slice_pos]
                key = None
                for key, value in DICT_REG_NUMBERS.items():
                    if value == self.backup[slice_pos]:
                        break
                self.picRGB[voxel[0], voxel[1]] = np.uint8(
                    np.minimum(self.nissl_img[voxel[0],
                                              voxel[1]] + 77 * np.array(DICT_REG_COLORS[key]), 255))

    def change_slice(self, coronal_pos):
        """
        Change the coronal position of the slice and regenerate the image.

        :param int coronal_pos: New position of the slice.
        """
        self.idX = coronal_pos
        self.generate_image()

    def fill(self, position, key):
        """
        Fill all voxels surrounding a voxel that belong to the same group.

        :param list position: Initial position.
        :param str key: Key of the DICT_REG_NUMBERS and DICT_REG_COLORS corresponding to the new
            value.
        """
        image = self.annCPY[self.idX, self.idsY[0]:self.idsY[1] + 1, self.idsZ[0]:self.idsZ[1] + 1]
        voxels_to_update = find_group(image, position, image[position[0], position[1]])
        self.update_slice(voxels_to_update, key)

    def apply_changes(self):
        """
        Save changes applied on the annotations. Update backup.
        """
        filter_ = self.annCPY != self.backup
        self.annotation[filter_] = self.inv_dict_reg_ids[self.annCPY[filter_]]
        self.backup = np.copy(self.annCPY)
