"""tools to deal with brain hierarchy from the AIBS"""
import numpy as np

id_to_region_dictionary = {}  # id to region name
id_to_region_dictionary_ALLNAME = {}  # id to complete name
region_dictionary_to_id = {}  # name to id
region_dictionary_to_id_ALLNAME = {}  # complete name to id

region_dictionary_to_id_ALLNAME_parent = {
}  # complete name to complete name parent
region_dictionary_to_id_parent = {}  # name to name parent
allname2name = {}  # complete name to name
name2allname = {}  # name to complete name
region_keys = []  # list of regions names
regions_ALLNAME_list = []  # list of complete regions names
is_leaf = {}  # full name to int (! if is leaf, else 0)
id_to_color = {}  # region id to color in RGB
region_to_color = {}  # complete name to color in RGB
id_to_abv = {}
region_dictionary_to_abv = {}


def find_unique_regions(annotation,
                        id_to_region_dictionary_ALLNAME,
                        region_dictionary_to_id_ALLNAME,
                        region_dictionary_to_id_ALLNAME_parent,
                        name2allname,
                        top_region_name="Basic cell groups and regions"):
    """
    Finds unique regions ids that are present in an annotation file
    and are contained in the top_region_name
    Adds also to the list each parent of the regions present in the annotation file.
    Dictionaries parameters correspond to the ones produced in JSONread

    Parameters:
        annotation: 3D numpy ndarray of integers ids of the regions
        id_to_region_dictionary_ALLNAME: dictionary from region id to region complete name
        region_dictionary_to_id_ALLNAME: dictionary from region complete name to region id
        region_dictionary_to_id_ALLNAME_parent: dictionary from region complete name
        to its parent complete name
        name2allname: dictionary from region name to region complete name
        top_region_name: name of the most broader region included in the uniques

    Returns:
        List of unique regions id in the annotation file that are included in top_region_name
    """

    # Take the parent of the top region to stop the loop
    root_allname = region_dictionary_to_id_ALLNAME_parent[name2allname[top_region_name]]
    uniques = []
    for uniq in np.unique(annotation)[1:]:  # Cell regions without outside
        allname = id_to_region_dictionary_ALLNAME[uniq]
        if top_region_name in id_to_region_dictionary_ALLNAME[uniq] and uniq not in uniques:
            uniques.append(uniq)
            parent_allname = region_dictionary_to_id_ALLNAME_parent[allname]
            id_parent = region_dictionary_to_id_ALLNAME[parent_allname]
            while id_parent not in uniques and parent_allname != root_allname:
                uniques.append(id_parent)
                parent_allname = region_dictionary_to_id_ALLNAME_parent[parent_allname]
                if parent_allname == "":
                    break
                id_parent = region_dictionary_to_id_ALLNAME[parent_allname]

    return np.array(uniques)


def find_children(uniques, id_to_region_dictionary_ALLNAME, is_leaf,
                  region_dictionary_to_id_ALLNAME_parent,
                  region_dictionary_to_id_ALLNAME):
    """
    Finds the children regions of each region id in uniques
    and its distance from a leaf region in the hierarchy tree.
    Non leaf regions are included in the children list
    Dictionaries parameters correspond to the ones produced in JSONread

    Parameters:
        uniques: List of unique region ids
        id_to_region_dictionary_ALLNAME: dictionary from region id to region complete name
        is_leaf: dictionary from region complete name to boolean,
        True if the region is a leaf region.
        region_dictionary_to_id_ALLNAME_parent: dictionary from region complete name
        to its parent complete name
        region_dictionary_to_id_ALLNAME: dictionary from region complete name to region id

    Returns:
         Dictionary of region complete name to list of child region ids
         List of distances from a leaf region in the hierarchy tree for each region in uniques.
    """

    children = {}
    order_ = np.zeros(uniques.shape)
    for id_reg, allname in id_to_region_dictionary_ALLNAME.items():
        if is_leaf[allname]:
            inc = 0
            ids_reg = [id_reg]
            parentname = region_dictionary_to_id_ALLNAME_parent[allname]
            while parentname != '':
                if parentname not in children:
                    children[parentname] = []
                children[parentname] += ids_reg
                inc += 1
                id_parent = region_dictionary_to_id_ALLNAME[parentname]
                if id_parent in uniques:
                    ids_reg.append(id_parent)
                    place_ = np.where(uniques == id_parent)
                    order_[place_] = max(order_[place_], inc)
                allname = parentname
                parentname = region_dictionary_to_id_ALLNAME_parent[allname]

    for parent, child in children.items():
        children[parent] = np.unique(child)
    return children, order_


def filter_region(annotation, allname, children,
                  is_leaf, region_dictionary_to_id_ALLNAME):
    """
    Computes a 3d boolean mask to filter a region and its subregion from the annotations.
    Dictionaries parameters correspond to the ones produced in JSONread.

    Parameters:
        annotation: 3D numpy ndarray of integers ids of the regions
        allname: Complete name of the region
        children: Dictionary of region complete name to list of child region ids
        is_leaf: dictionary from region complete name to boolean,
        True if the region is a leaf region.
        region_dictionary_to_id_ALLNAME: dictionary from region complete name to region id

    Returns:
        3d numpy ndarray of boolean, boolean mask with all the voxels of a region
        and its children set to True.
    """
    if not is_leaf[allname]:
        filter_ = np.in1d(annotation,
                          np.concatenate((children[allname],
                                          [region_dictionary_to_id_ALLNAME[allname]]))
                          ).reshape(annotation.shape)
    else:
        filter_ = annotation == region_dictionary_to_id_ALLNAME[allname]
    return filter_


def return_ids_containing_str_list(str_list, force_leaf=False):
    """
    Retrieve the list of region id which complete name contains all the keywords in str_list.

    Arguments:
        str_list: List of keyword that the region complete name.
    Returns:
        List of region id matching condition
    """

    id_list = []
    for kk in id_to_region_dictionary_ALLNAME:
        region_is_in = True
        allname = id_to_region_dictionary_ALLNAME[kk]
        if force_leaf and not is_leaf[allname]:
            continue
        for str1 in str_list:
            if (allname.lower()).find(str1.lower(
            )) < 0:  # if any of the regions is not there, do not take
                region_is_in = False
                break
        if region_is_in:
            id_list.append(kk)
    return id_list


def hex_to_rgb(value):
    """
    Converts a Hexadecimal color into its RGB value counterpart.

    Arguments:
        value: string hexadecimal color to convert.
    Returns:
        List of the Red, Green, and Blue components of the color
    """

    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb2hex(rgb):
    return '{:02x}{:02x}{:02x}'.format(*np.rint(rgb).astype(int))


def search_children(object_,
                    lastname_ALL="",
                    lastname="",
                    darken=True):
    """
    Explores the hierarchy dictionary to extract its brain regions and fills external dictionaries.
    Arguments
        object_: dictionary of regions properties. See
        https://bbpteam.epfl.ch/documentation/projects/voxcell/latest/atlas.html#brain-region-hierarchy
        lastname_ALL: complete name of the parent of the current brain region
        lastname: name of the parent of the current brain region
        darken: if True, darkens the region colors too high
    """

    regions_ALLNAME_list.append(lastname_ALL + "|" + object_["name"])
    name2allname[object_["name"]] = lastname_ALL + "|" + object_["name"]
    allname2name[lastname_ALL + "|" + object_["name"]] = object_["name"]
    id_to_region_dictionary[object_["id"]] = object_["name"]
    id_to_abv[object_["id"]] = object_["acronym"]
    id_to_region_dictionary_ALLNAME[
        object_["id"]] = lastname_ALL + "|" + object_["name"]
    region_dictionary_to_id[object_["name"]] = object_["id"]
    region_dictionary_to_abv[object_["name"]] = object_["acronym"]
    region_dictionary_to_id_ALLNAME[lastname_ALL + "|" +
                                    object_["name"]] = object_["id"]
    region_dictionary_to_id_ALLNAME_parent[lastname_ALL + "|" +
                                           object_["name"]] = lastname_ALL
    region_dictionary_to_id_parent[object_["name"]] = lastname
    clrTMP = np.float32(
        np.array(list(hex_to_rgb(object_["color_hex_triplet"]))))
    if np.sum(clrTMP) > 255.0 * 3.0 * 0.75 and darken:
        clrTMP *= 255.0 * 3.0 * 0.75 / np.sum(clrTMP)
    region_to_color[lastname_ALL + "|" + object_["name"]] = list(clrTMP)
    id_to_color[object_["id"]] = list(clrTMP)
    region_keys.append(object_["name"])
    try:
        is_leaf[lastname_ALL + "|" + object_["name"]] = 1
        # ~ region_dictionary_to_id_ALLNAME_child[  lastname_ALL+"|"+object_["name"] ] = children
        # ~ id_children[object_["id"]] = object_["children"]
        for children in object_["children"]:
            search_children(children,
                            lastname_ALL + "|" + object_["name"],
                            object_["name"], darken=darken)
            is_leaf[lastname_ALL + "|" + object_["name"]] = 0
    except KeyError:
        print("No children of object")

allnameOrder = {}; iterTMP = 0

def readSpinal(content):
    global iterTMP, region_keys
    
    for line in content:
        id_to_region_dictionary[line["id"]] = line["name"]
        id_to_region_dictionary_ALLNAME[line["id"]] = line["full_name"]
        region_dictionary_to_id[line["name"]] = line["id"]
        region_dictionary_to_id_ALLNAME[line["full_name"]] = line["id"]

        region_dictionary_to_id_ALLNAME_parent[line["full_name"]] = line["full_name"].rsplit("|", 1)[1] 
        region_dictionary_to_id_parent[line["name"]] = id_to_region_dictionary[line["parent"]]
        allname2name [line["full_name"]]= line["name"]
        name2allname [line["name"]] = line["full_name"]
        allnameOrder [line["full_name"]] = iterTMP; iterTMP+=1
        region_keys.append(line["name"])
        regions_ALLNAME_list.append(line["full_name"])
        is_leaf[line["full_name"]] = line["is_leaf"]
        # regions_pos[line["name"]] = 
        id_to_color[line["id"]] = line["color"]
        region_to_color[line["name"]] = line["color"]
