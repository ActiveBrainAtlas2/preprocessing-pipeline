
import os, sys
import numpy as np
from collections import OrderedDict
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
sqlController = SqlController('DK43')
from utilities.file_location import DATA_PATH

col_length = 1000
row_length = 1000
z_length = 300
atlas_box_size=(row_length, col_length, z_length)
atlas_box_scales=(10, 10, 20)
atlas_raw_scale=10

atlas_name = 'atlas'
atlas_centers = sqlController.get_centers_dict(atlas_name)
#atlas_centers['DC_L'] = [83,-43,-215]
#atlas_centers['DC_R'] = [83,-43,215]
#atlas_centers['SC'] = [-128,-241,3]
atlas_box_scales = np.array(atlas_box_scales)
atlas_box_size = np.array(atlas_box_size)
atlas_box_center = atlas_box_size / 2
com_bili = OrderedDict()
for structure, origin in atlas_centers.items():
    x,y,section = atlas_box_center + np.array(origin) * atlas_raw_scale / atlas_box_scales
    com_bili[structure] = [int(x),int(y),int(section)]

ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
ORIGIN_PATH = os.path.join(ATLAS_PATH, 'origin')
VOLUME_PATH = os.path.join(ATLAS_PATH, 'structure')

origin_files = sorted(os.listdir(ORIGIN_PATH))
volume_files = sorted(os.listdir(VOLUME_PATH))

structure_volume_origin = {}
for volume_filename, origin_filename in zip(volume_files, origin_files):
    structure = os.path.splitext(volume_filename)[0]
    origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
    volume_path = os.path.join(VOLUME_PATH, volume_filename)

    volume = np.load(volume_path)
    volume = np.rot90(volume, axes=(0, 1))
    volume = np.flip(volume, axis=0)
    volume = volume.astype(np.uint8)
    structure_volume_origin[structure] = (volume, origin)

common_keys = com_bili.keys() & structure_volume_origin.keys()
com_existing = OrderedDict()
for structure, (volume, origin) in sorted(structure_volume_origin.items()):
    if structure not in common_keys:
        continue

    x, y, z = origin
    x_start = x + col_length / 2
    y_start = y + row_length / 2
    z_start = z / 2 + z_length / 2
    x_end = x_start + volume.shape[0]
    y_end = y_start + volume.shape[1]
    z_end = z_start + (volume.shape[2] + 1) / 2
    midx = ((x_start + x_end) / 2)
    midy = ((y_start + y_end) / 2)
    midz = (z_start + z_end) / 2

    com_existing[structure] = [midx, midy, midz]

for (kb,vb),(ke,ve) in zip(com_bili.items(), com_existing.items()):
    arrb = np.array(vb)
    arre = np.array(ve)
    if kb == ke:
        diffed = np.array(arrb-arre).astype(np.int)
        print(kb, end="\t")
        print(diffed)
