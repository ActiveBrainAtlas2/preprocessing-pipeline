"""
Takes as input a key-id to structure string mapping (as in struct_key.json) and converts it to a
json format to be used by neuroglancer
"""

import json

INPUT_KEY_LOC = 'structure_key_full.json'
OUTPUT_LOC = 'segmentation_prop_info.json'
NUM_STRUCTS = 49
with open(INPUT_KEY_LOC, 'r') as f:
    struct_keys = json.load(f)


segmentation_info = dict()
segmentation_info['@type'] = 'neuroglancer_segment_properties'
segmentation_info['inline'] = dict()
segmentation_info['inline']['ids'] = list(map(lambda x: str(x), list(range(1, NUM_STRUCTS+1))))
segmentation_info['inline']['properties'] = list()

# Create Labels
labels = dict()
labels['id'] = 'label'
labels['type'] = 'label'
labels['description'] = 'Names of Structures'
labels['values'] = list()
for i in range(1, NUM_STRUCTS+1):
    labels['values'].append(struct_keys[str(i)])

desc = dict()
desc['id'] = 'description'
desc['type'] = 'description'
desc['description'] = 'Information on Structures'
desc['values'] = list()

for i in range(1, NUM_STRUCTS+1):
    desc['values'].append(f"This is {struct_keys[str(i)]} with key {i}")

segmentation_info['inline']['properties'].extend([labels, desc])


with open(OUTPUT_LOC, 'w+') as f:
    json.dump(segmentation_info, f)

print(f"File generated at {OUTPUT_LOC}")
