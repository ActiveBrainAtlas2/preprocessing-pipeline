import os
import sys
import numpy as np
from timeit import default_timer as timer
import collections
from pymicro.view.vol_utils import compute_affine_transform


start = timer()
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties

animal = 'DK52'
fileLocationManager = FileLocationManager(animal)
atlas_name = 'atlasV7'
DATA_PATH = '/net/birdstore/Active_Atlas_Data/data_root'
ROOT_DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data'
THUMBNAIL_DIR = os.path.join(ROOT_DIR, animal, 'preps', 'CH1', 'thumbnail')
ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
ORIGIN_PATH = os.path.join(ATLAS_PATH, 'origin')
VOLUME_PATH = os.path.join(ATLAS_PATH, 'structure')
OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'atlas')
os.makedirs(OUTPUT_DIR, exist_ok=True)

origin_files = sorted(os.listdir(ORIGIN_PATH))
volume_files = sorted(os.listdir(VOLUME_PATH))

structure_volume_origin = {}
for volume_filename, origin_filename in zip(volume_files, origin_files):
    structure = os.path.splitext(volume_filename)[0]
    if structure not in origin_filename:
        print(structure, origin_filename)
        break

    color = get_structure_number(structure.replace('_L', '').replace('_R', ''))

    origin = np.loadtxt(os.path.join(ORIGIN_PATH, origin_filename))
    volume = np.load(os.path.join(VOLUME_PATH, volume_filename))

    volume = np.rot90(volume, axes=(0, 1))
    volume = np.flip(volume, axis=0)
    volume[volume > 0.8] = color
    volume = volume.astype(np.uint8)

    structure_volume_origin[structure] = (volume, origin)
#print(structure_volume_origin.keys())


#x_length = 1000
#y_length = 1000
#z_length = 300
animal = 'DK52'
sqlController = SqlController(animal)
resolution = sqlController.scan_run.resolution
aligned_shape = np.array((sqlController.scan_run.width, sqlController.scan_run.height))
z_length = len(os.listdir(THUMBNAIL_DIR))

downsampled_aligned_shape = np.round(aligned_shape / 32).astype(int)

x_length = downsampled_aligned_shape[1]
y_length = downsampled_aligned_shape[0]

atlasV7_volume = np.zeros((x_length, y_length, z_length), dtype=np.uint32)
my_structures = {'SC': [24226, 6401, 220],
 'DC_L': [24482, 11985, 134, 104, 165],
 'DC_R': [20424, 11736, 330],
 'LC_L': [25290, 11750, 180, 175, 185],
 'LC_R': [24894, 12079, 268],
 '5N_L': [23790, 13025, 160, 150, 170],
 '5N_R': [20805, 14163, 298],
 '7n_L': [20988, 18405, 177, 148, 206],
 '7n_R': [24554, 13911, 284]}
animal_origin = collections.OrderedDict()
for structure, origin in sorted(my_structures.items()):
    animal_origin[structure] = [my_structures[structure][1]/32,
                                    my_structures[structure][0]/32,
                                    my_structures[structure][2]]

atlas_origin = collections.OrderedDict()

for structure, (volume, origin) in sorted(structure_volume_origin.items()):
    x, y, z = origin
    x_start = int(x) + x_length // 2
    y_start = int(y) + y_length // 2
    z_start = int(z) // 2 + z_length // 2
    x_end = x_start + volume.shape[0]
    y_end = y_start + volume.shape[1]
    z_end = z_start + (volume.shape[2] + 1) // 2
    midx = round((x_end + x_start) / 2)
    midy = round((y_end + y_start) / 2)
    midz = round((z_end + z_start) / 2)



    if structure in animal_origin.keys():
        print('atlas', structure, midx,midy,midz, 'md589',animal_origin[structure])

        atlas_origin[structure] = [midx, midy, midz]

atlas_origin_array = np.array(list(atlas_origin.values()), dtype=np.float32)
animal_origin_array = np.array(list(animal_origin.values()), dtype=np.float32)

origin_centroid = np.mean(animal_origin_array, axis=0)
fitted_centroid = np.mean(atlas_origin_array, axis=0)
print('origin centroid', origin_centroid, 'fitted centroid', fitted_centroid)
# compute the affine transform from the point set
translation, transformation = compute_affine_transform(animal_origin_array, atlas_origin_array)
invt = np.linalg.inv(transformation)
offset = -np.dot(invt, translation)


for structure, (volume, origin) in sorted(structure_volume_origin.items()):
    x, y, z = origin
    x_start = int(x) + x_length // 2
    y_start = int(y) + y_length // 2
    z_start = int(z) // 2 + z_length // 2
    # do transformation
    xyz = np.array([x_start,y_start,z_start], dtype=np.float32)
    #new_points[i] = origin_centroid + np.dot(transformation, fitted[i] - fitted_centroid)
    x_start, y_start, z_start = origin_centroid + np.dot(transformation, xyz - fitted_centroid)
    x_start = int(round(x_start))
    y_start = int(round(y_start))
    z_start = int(round(z_start))
    print('x', x_start, 'y', y_start, 'z', z_start)

    x_end = x_start + volume.shape[0]
    y_end = y_start + volume.shape[1]
    z_end = z_start + (volume.shape[2] + 1) // 2

    z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
    volume = volume[:, :, z_indices]
    atlasV7_volume[x_start:x_end, y_start:y_end, z_start:z_end] += volume


ng = NumpyToNeuroglancer(atlasV7_volume, [10000, 10000, 20000])
ng.init_precomputed(OUTPUT_DIR)
ng.add_segment_properties(get_segment_properties())
ng.add_downsampled_volumes()
ng.add_segmentation_mesh()


end = timer()
print(f'Finito! Program took {end - start} seconds')

#outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.npy')
#with open(outpath, 'wb') as file:
#    np.save(file, atlasV7_volume)

