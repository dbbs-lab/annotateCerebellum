from os.path import join
import json
from annotate_cerebellum.paint_tools import PaintAnnotations
from annotate_cerebellum.utils import *
from JSONread import *

# Path to the files (can be either nrrd files or numpy files)
DATA_FOLDER = "data"
nissl_filename = join(DATA_FOLDER, "ara_nissl_25.nrrd")
annotation_filename = join(DATA_FOLDER, "annotation_corrected_clfd.npy")
hierarchy_filename = join(DATA_FOLDER, "brain_regions.json")
output_filename = join(DATA_FOLDER, "annotation_corrected_clfd.npy")

# Protected regions
protected_regions = ["Lingula (I)", "Flocculus", "Crus 1"]

# Load json hierarchy file
jsontextfile = open(hierarchy_filename, "r")
jsoncontent = json.loads(jsontextfile.read())
search_children(jsoncontent['msg'][0])

# Load Nissl and annotations
nissl = load_nrrd_npy_file(nissl_filename)
ann = load_nrrd_npy_file(annotation_filename)

u_regions = find_unique_regions(ann, id_to_region_dictionary_ALLNAME,
                                region_dictionary_to_id_ALLNAME,
                                region_dictionary_to_id_ALLNAME_parent, name2allname)
children, _ = find_children(u_regions, id_to_region_dictionary_ALLNAME, is_leaf,
                            region_dictionary_to_id_ALLNAME_parent, region_dictionary_to_id_ALLNAME)
ids_prot = []
for region in protected_regions:
    ids_prot.extend(children[name2allname[region]])

ids_mol = return_ids_containing_str_list(["Cerebellar cortex", "molecular"], True)
ids_FT = return_ids_containing_str_list(["cerebellum related fiber tracts"], True)

for i, id_ in enumerate(ids_mol[1:]):
    print(i, region_dictionary_to_id_parent[id_to_region_dictionary[id_]])

i = int(input("Enter the number of the region to correct "))
id_mol = ids_mol[i + 1]
parent_name = region_dictionary_to_id_parent[id_to_region_dictionary[id_mol]]
print("You have selected:")
print(i, parent_name)
print("")
axes = ["coronal", "axial", "sagittal"]
for i, id_ in enumerate(axes):
    print(i, id_)
i = int(input("Enter the number of the axis to display "))
axis = i
print("You have selected:")
print(i, axes[i])

# Lift the protection on the region if it is selected.
ids_prot = np.delete(ids_prot, np.isin(ids_prot, children[name2allname[parent_name]]))

parent_name = region_dictionary_to_id_ALLNAME_parent[id_to_region_dictionary_ALLNAME[id_mol]]
last_name = parent_name[parent_name.rfind("|") + 1:]
id_gr = region_dictionary_to_id_ALLNAME[parent_name + "|" + last_name + ", granular layer"]

paintAppli = PaintAnnotations(ann, nissl,
                              {
                                  "mol": [id_mol],
                                  "gl": [id_gr],
                                  "fib": ids_FT,
                                  "out": [0],
                                  "prot": ids_prot
                              },
                              axis)

ann = paintAppli.get_annotations()
save_nrrd_npy_file(output_filename, ann, header=DEFAULT_HEADER)
