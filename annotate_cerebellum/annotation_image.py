import numpy as np

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


def find_group(image, position, id_reg):
    explored = np.zeros(image.shape, dtype=bool)
    to_explore = [position]
    list_position = []
    while len(to_explore) > 0:
        current_pos = to_explore.pop()
        explored[current_pos[0], current_pos[1]] = True
        if image[current_pos[0], current_pos[1]] == id_reg:
            list_position.append(current_pos)
            for x in range(-1, 2):
                for y in range(-1, 2):
                    new_vox = [current_pos[0] + x, current_pos[1] + y]
                    if not explored[new_vox[0], new_vox[1]] and new_vox not in to_explore:
                        to_explore.append(new_vox)
    return np.array(list_position)


class AnnotationImage:
    def __init__(self, annotation, dict_reg_ids, nissl):
        self.annotation = annotation
        self.nissl = nissl
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

        filter_ = np.where(np.isin(self.annCPY, [DICT_REG_NUMBERS["mol"], DICT_REG_NUMBERS["gl"]]))
        self.idsX = [np.min(filter_[0]) - 1, np.max(filter_[0]) + 1]
        self.idsY = [max(0, np.min(filter_[1] - 80)),
                     min(int(annotation.shape[1]) - 1, np.max(filter_[1] + 80))]
        self.idsZ = [max(0, np.min(filter_[2] - 120)),
                     min(int(annotation.shape[2]) - 1, np.max(filter_[2] + 120))]
        self.idX = int(np.mean(filter_[0]))
        self.generate_image()

    def generate_image(self):
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
        for voxel in voxels_to_update:
            slice_pos = np.s_[self.idX, self.idsY[0] + voxel[0], self.idsZ[0] + voxel[1]]
            if 0 <= voxel[0] < self.picRGB.shape[0] and \
               0 <= voxel[1] < self.picRGB.shape[1] and \
               not self.annCPY[slice_pos] == DICT_REG_NUMBERS["prot"]:
                self.annCPY[slice_pos] = DICT_REG_NUMBERS[key]
                self.picRGB[voxel[0], voxel[1]] = np.uint8(
                    np.minimum(self.nissl_img[voxel[0],
                                              voxel[1]] + 77 * np.array(DICT_REG_COLORS[key]), 255))

    def revert_slice(self, voxels_to_update):
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
        self.idX = coronal_pos
        self.generate_image()

    def fill(self, position, key):
        image = self.annCPY[self.idX, self.idsY[0]:self.idsY[1] + 1, self.idsZ[0]:self.idsZ[1] + 1]
        voxels_to_update = find_group(image, position, image[position[0], position[1]])
        self.update_slice(voxels_to_update, key)

    def apply_changes(self):
        filter_ = self.annCPY != self.backup
        self.annotation[filter_] = self.inv_dict_reg_ids[self.annCPY[filter_]]
        self.backup = np.copy(self.annCPY)
