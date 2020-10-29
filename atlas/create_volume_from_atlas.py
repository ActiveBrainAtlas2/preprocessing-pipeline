"""
Scale with 32 on DK52, x is 1125, y is 2031
SCALE with 10/resolution  on DK52, x is 1170, y 2112
scale with 10/resolution on MD589, x is 1464, y 1975
"""
import argparse
import os
import sys
import numpy as np
from timeit import default_timer as timer
from _collections import OrderedDict
import shutil
from pprint import pprint
start = timer()
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties
from utilities.utilities_affine import align_point_sets, load_atlas_data, estimate_structure_centers, umeyama, \
    rigid_transform_3D


def create_atlas(animal, create):
    fileLocationManager = FileLocationManager(animal)
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'atlas')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    atlas_data = load_atlas_data()
    source_centers = estimate_structure_centers(atlas_data, animal)
    # DK52 structure centers
    output_centers = {
        '12N': [46488, 18778, 242],
        '5N_L': [38990, 20019, 172],
        '5N_R': [39184, 19027, 315],
        '7N_L': [42425, 23190, 166],
        '7N_R': [42286, 22901, 291]
    }
    structures = sorted(output_centers.keys())
    source_point_set = np.array([source_centers[s] for s in structures]).T
    # Unify to 1 mum scale in all axes
    source_scale = np.diagflat([10, 10, 20])
    #source_point_set = source_scale @ source_point_set
    output_point_set = np.array([output_centers[s] for s in structures]).T
    pprint(output_centers)
    pprint(source_centers)
    # Unify to 1 mum scale in all axes
    #output_scale = np.diagflat([0.325, 0.325, 0.325])
    output_scale = np.array([0.325, 0.325, 0.325])
    #output_point_set = output_scale @ output_point_set
    r_auto, t_auto = align_point_sets(source_point_set, output_point_set)
    #t_auto_out = (np.linalg.inv(output_scale) @ t_auto).T
    #r_auto[2][2] = 1
    pprint(r_auto)
    pprint(t_auto)

    #for structure, (volume, origin) in sorted(structure_volume_origin.items()):
    for structure, source_point in sorted(source_centers.items()):
        print(str(structure).ljust(6), end=": ")
        results = (r_auto @ source_point + t_auto.T).reshape(1,3)
        print(results*0.325,end="\n")
        continue

        x, y, z = origin
        arr = np.array([y, x, z])
        input = arr + t
        results = np.dot(r_auto, input.T).reshape(3,1)
        y = results[0][0]
        x = results[1][0]
        z = results[2][0]
        x_start = int(round(x + col_length / 2))
        y_start = int(round(y + row_length / 2))
        z_start = int(round(z / 2 + z_length / 2))
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = int(z_start + (volume.shape[2] + 1) / 2)

        print('Y', str(y_start).rjust(4),  str(y_end).rjust(4),
              'X',  str(x_start).rjust(4), str(x_end).rjust(4),
              'Z',  str(z_start).rjust(4), str(z_end).rjust(4),
              end=" ")

        print()
        continue
        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]
        volume = np.swapaxes(volume, 0, 1)

        try:
            atlasV7_volume[y_start:y_end, x_start:x_end, z_start:z_end] += volume
        except ValueError as ve:
            print(ve, end=" ")

        print()


    #resolution = int(resolution * 1000 * SCALE)
    print('Shape of downsampled atlas volume after swapping'.ljust(60), atlasV7_volume.shape)
    resolution = 10000
    print('Resolution at', resolution)

    if create:
        atlasV7_volume = np.rot90(atlasV7_volume, axes=(0, 1))
        atlasV7_volume = np.fliplr(atlasV7_volume)
        atlasV7_volume = np.flipud(atlasV7_volume)
        atlasV7_volume = np.fliplr(atlasV7_volume)
        print('Shape of downsampled atlas volume after rotating/flipping'.ljust(60), atlasV7_volume.shape)

        offset =  [0,0,0]
        ng = NumpyToNeuroglancer(atlasV7_volume, [resolution, resolution, 20000], offset=offset)
        ng.init_precomputed(OUTPUT_DIR)
        ng.add_segment_properties(get_segment_properties())
        ng.add_downsampled_volumes()
        ng.add_segmentation_mesh()

        #outpath = os.path.join(ATLAS_PATH, f'{atlas_name}.tif')
        #io.imsave(outpath, atlasV7_volume.astype(np.uint8))
    end = timer()
    print(f'Finito! Program took {end - start} seconds')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=False, default='DK52')
    parser.add_argument('--create', help='create volume', required=False, default='false')
    args = parser.parse_args()
    animal = args.animal
    create = bool({'true': True, 'false': False}[args.create.lower()])
    create_atlas(animal, create)

