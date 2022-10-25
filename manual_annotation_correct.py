import sys
from os.path import join
import nrrd
import json
from annotate_cerebellum.paint_tools import PaintAnnotations
from JSONread import *

if len(sys.argv) < 2:
    print('The data folder path is required')
    sys.exit(1)
DATA_FOLDER = sys.argv[-1]

protected_regions = ["Lingula (I)", "Flocculus", "Crus 1"]

# Load json hierarchy file
jsontextfile = open(join(DATA_FOLDER, "brain_regions.json"), "r")
jsoncontent = json.loads(jsontextfile.read())
search_children(jsoncontent['msg'][0])

# Load Nissl and annotations
nissl, h = nrrd.read(join(DATA_FOLDER, "ara_nissl_25.nrrd"))
ann = np.load(join(DATA_FOLDER, 'annotation_corrected_clfd.npy'))

ids_mol = return_ids_containing_str_list(["Cerebellar cortex", "molecular"], True)
ids_FT = return_ids_containing_str_list(["cerebellum related fiber tracts"], True)

ids_prot = []
for name in protected_regions:
    for child, parent in region_dictionary_to_id_parent.items():
        if parent == name:
            ids_prot.append(region_dictionary_to_id[child])

for i, id_ in enumerate(ids_mol[1:]):
    print(i, region_dictionary_to_id_parent[id_to_region_dictionary[id_]])

i = int(input("Enter the number of the region to correct "))
id_mol = ids_mol[i + 1]
print("You have selected:")
print(i, region_dictionary_to_id_parent[id_to_region_dictionary[id_mol]])

parent_name = region_dictionary_to_id_ALLNAME_parent[id_to_region_dictionary_ALLNAME[id_mol]]
last_name = parent_name[parent_name.rfind("|") + 1:]
id_gr = region_dictionary_to_id_ALLNAME[parent_name + "|" + last_name + ", granular layer"]

paintAppli = PaintAnnotations(ann, nissl, {
    "mol": [id_mol],
    "gl": [id_gr],
    "fib": ids_FT,
    "out": [0],
    "prot": ids_prot
    })

ann = paintAppli.get_annotations()
np.save(join(DATA_FOLDER, 'annotation_corrected_clfd.npy'), ann)
