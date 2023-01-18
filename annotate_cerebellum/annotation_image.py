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
    "corrected": 5,
}

DICT_REG_COLORS = {
    "mol": (0, 1, 0),
    "gl": (1, 0, 0),
    "fib": (0, 0, 1),
    "out": (0, 0, 0),
    "prot": (1, 0, 1),
    "corrected": (1, 1, 0),
}


class AnnotationImage:
    """
    Class of the model of the user application to modify volumetric cerebellar annotations.
    Applies modification on the annotations.
    """

    def __init__(self, annotation, dict_reg_ids, nissl, axis=0, backup=None):
        """
        Initialize the annotation model class.

        :param ndarray annotation: Volumetric array of integers corresponding to brain region ids
        :param dict dict_reg_ids: Dictionary linking keys of DICT_REG_NUMBERS and DICT_REG_COLORS to
            their list brain region ids
        :param ndarray nissl: Volumetric array of float corresponding to nissl expression
        """
        self.annotation = annotation
        self.orig_ann = backup
        self.nissl = np.copy(nissl)
        if self.nissl.shape != self.annotation.shape:
            raise Exception("The annotation and nissl volumes must have the same shape.")
        if backup is not None and self.annotation.shape != backup.shape:
            raise Exception("The annotation and backup volumes must have the same shape.")
        self.dict_reg_ids = dict_reg_ids
        self.inv_dict_reg_ids = np.zeros(np.max(list(DICT_REG_NUMBERS.values())) + 1, dtype=int)
        self.inv_dict_reg_ids[DICT_REG_NUMBERS["mol"]] = self.dict_reg_ids["mol"][0]
        self.inv_dict_reg_ids[DICT_REG_NUMBERS["gl"]] = self.dict_reg_ids["gl"][0]
        self.inv_dict_reg_ids[DICT_REG_NUMBERS["fib"]] = self.dict_reg_ids["fib"][0]

        if not 0 <= axis <= 2:
            raise Exception(("The axis value is incorrect: {}. "
                             "Only 3 dimensions are possible").format(axis))
        self.axis = axis
        self.annCPY = np.zeros(annotation.shape, np.int8)
        self.annCPY[self.annotation > 0] = -1
        for key, value in DICT_REG_NUMBERS.items():
            if key in self.dict_reg_ids:
                self.annCPY[np.isin(self.annotation, self.dict_reg_ids[key])] = value
        offsets = [80, 80, 120]
        offsets[axis] = 1
        if backup is not None:
            self.backup = np.zeros(annotation.shape, np.int8)
            self.backup[backup > 0] = -1
            for key, value in DICT_REG_NUMBERS.items():
                if key in self.dict_reg_ids:
                    self.backup[np.isin(backup, self.dict_reg_ids[key])] = value
        else:
            self.backup = np.copy(self.annCPY)
        self.annCPY[(self.annCPY == DICT_REG_NUMBERS["out"]) *
                    (self.backup != self.annCPY)] = DICT_REG_NUMBERS["corrected"]
        if self.axis == 2:
            self.annCPY = self.annCPY.swapaxes(0, 1)
            self.backup = self.backup.swapaxes(0, 1)
            self.nissl = self.nissl.swapaxes(0, 1)
            offsets = [offsets[1], offsets[0], offsets[2]]
        self.previous_state = np.copy(self.annCPY)

        filter_ = np.where(np.isin(self.annCPY, [DICT_REG_NUMBERS["mol"], DICT_REG_NUMBERS["gl"]]))
        self.ids = np.zeros((3, 2), dtype=int)
        for i in range(3):
            self.ids[i] = [max(0, np.min(filter_[i] - offsets[i])),
                           min(int(self.annCPY.shape[i]) - 1, np.max(filter_[i] + offsets[i]))]
        self.slice_pos = int(np.mean(filter_[axis]))
        self.generate_image()

    def get_slice(self):
        """
        Get the slice indexes in the volume for the image to display

        :return: slice of the image to display
        :rtype: np.IndexExpression
        """
        if self.axis == 0:
            return np.s_[self.slice_pos,
                         self.ids[1, 0]:self.ids[1, 1] + 1,
                         self.ids[2, 0]:self.ids[2, 1] + 1]
        elif self.axis == 1:
            return np.s_[self.ids[0, 0]:self.ids[0, 1] + 1,
                         self.slice_pos,
                         self.ids[2, 0]:self.ids[2, 1] + 1]
        elif self.axis == 2:
            return np.s_[self.ids[0, 0]:self.ids[0, 1] + 1,
                         self.ids[1, 0]:self.ids[1, 1] + 1,
                         self.slice_pos]
        else:
            raise Exception(("The axis value is incorrect: {}. "
                             "Only 3 dimensions are possible").format(self.axis))

    def get_position(self, pixel):
        """
        Get the voxel index in the volume for the pixel chosen

        :param list pixel: List of the position of the voxel of interest
        :return: index of the voxel
        :rtype: np.IndexExpression
        """
        if self.axis == 0:
            return np.s_[self.slice_pos, self.ids[1, 0] + pixel[0], self.ids[2, 0] + pixel[1]]
        if self.axis == 1:
            return np.s_[self.ids[0, 0] + pixel[0], self.slice_pos, self.ids[2, 0] + pixel[1]]
        if self.axis == 2:
            return np.s_[self.ids[0, 0] + pixel[0], self.ids[1, 0] + pixel[1], self.slice_pos]

    def generate_image(self):
        """
        Generate a 2D RGB image which correspond to the current coronal slice.
        """
        slice_pos = self.get_slice()
        self.picRGB = np.zeros((self.annCPY[slice_pos].shape[0],
                                self.annCPY[slice_pos].shape[1], 3), np.uint16)
        max_nissl = np.max(self.nissl[slice_pos])
        if max_nissl > 0:
            self.picRGB[:, :, 0] = self.picRGB[:, :, 1] = self.picRGB[:, :, 2] = np.uint16(
                255.0 * (self.nissl[slice_pos] / max_nissl))
        else:
            self.picRGB[:, :, 0] = self.picRGB[:, :, 1] = self.picRGB[:, :, 2] = 0

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
            slice_pos = self.get_position(voxel)
            if 0 <= voxel[0] < self.picRGB.shape[0] and \
                    0 <= voxel[1] < self.picRGB.shape[1] and \
                    not self.annCPY[slice_pos] == DICT_REG_NUMBERS["prot"] and \
                    self.annCPY[slice_pos] != DICT_REG_NUMBERS[key]:
                if not change:
                    self.previous_state = np.copy(self.annCPY)
                    change = True
                if key == "out" and DICT_REG_NUMBERS[key] != self.backup[slice_pos]:
                    key = "corrected"
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
            slice_pos = self.get_position(voxel)
            if 0 <= voxel[0] < self.picRGB.shape[0] and \
                    0 <= voxel[1] < self.picRGB.shape[1] and \
                    not self.annCPY[slice_pos] == DICT_REG_NUMBERS["prot"]:
                self.annCPY[slice_pos] = self.backup[slice_pos]
                if self.annCPY[slice_pos] >= 0:
                    key = None
                    for loc_key, value in DICT_REG_NUMBERS.items():
                        if value == self.backup[slice_pos]:
                            key = loc_key
                            break
                    if key:
                        self.picRGB[voxel[0], voxel[1]] = np.uint8(np.minimum(
                            self.nissl_img[voxel[0],
                                           voxel[1]] + 77 * np.array(DICT_REG_COLORS[key]), 255))
                else:
                    self.picRGB[voxel[0], voxel[1]] = np.uint8(self.nissl_img[voxel[0], voxel[1]])

    def change_slice(self, new_pos):
        """
        Change the position of the slice and regenerate the image.

        :param int new_pos: New position of the slice.
        """
        self.slice_pos = new_pos
        self.generate_image()

    def fill(self, position, key):
        """
        Fill all voxels surrounding a voxel that belong to the same group.

        :param list position: Initial position.
        :param str key: Key of the DICT_REG_NUMBERS and DICT_REG_COLORS corresponding to the new
            value.
        """
        slice_pos = self.get_slice()
        image = self.annCPY[slice_pos]
        voxels_to_update = find_group(image, position, image[position[0], position[1]])
        self.update_slice(voxels_to_update, key)

    def apply_changes(self):
        """
        Save changes applied on the annotations. Update backup.
        """
        filter_ = np.where(self.annCPY != self.backup)

        filter_ann = (filter_[1], filter_[0], filter_[2]) if self.axis == 2 else filter_
        self.annotation[filter_ann] = self.inv_dict_reg_ids[self.annCPY[filter_]]
        filter_ = np.where(self.annCPY == self.backup)
        filter_ann = (filter_[1], filter_[0], filter_[2]) if self.axis == 2 else filter_
        self.annotation[filter_ann] = self.orig_ann[filter_ann]
        self.backup = np.copy(self.annCPY)
