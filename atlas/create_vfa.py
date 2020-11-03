"""
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
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer, get_segment_properties
from utilities.utilities_affine import align_point_sets, get_atlas_centers, DATA_PATH, DK52_centers


def create_atlas(animal, create):

    sql_controller = SqlController(animal)
    fileLocationManager = FileLocationManager(animal)
    atlas_name = 'atlasV7'
    ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', atlas_name)
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'atlas')
    if os.path.exists(OUTPUT_DIR) and create:
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    resolution = sql_controller.scan_run.resolution
    SCALE = (10 / resolution)

    atlas_centers = get_atlas_centers()
    reference_centers = DK52_centers
    structures = sorted(reference_centers.keys())
    src_point_set = np.array([atlas_centers[s][0] for s in structures]).T
    atlas_box_scales = np.array([10, 10, 20])
    src_point_set = np.diag(atlas_box_scales) @ src_point_set
    dst_point_set = np.array([reference_centers[s] for s in structures]).T


    #####Transform to auto align
    R, t = align_point_sets(src_point_set, dst_point_set)
    reference_scales = (0.325, 0.325, 20)
    output_scale = np.diag(reference_scales)

    #x_out = inv(output_scale) @ x
    #x can be replaced by output_point_set_expected_auto or t_auto.
    all_atlas_centers = [a[0] for a in atlas_centers.values()]
    arr = np.array(all_atlas_centers).T
    x = R @ arr + t
    #x_out = np.linalg.inv(output_scale) @ x
    R = np.array([[0.99539957,  0.36001948,  0.01398446],
                  [-0.35951649,  0.99520404, - 0.03076857],
                 [-0.02361111,0.02418234,1.05805842]])
    t = np.array([[19186.25529129],
                  [9825.28539829],
                  [78.18301303]])


    rotationpath = os.path.join(ATLAS_PATH, f'atlas2{animal}.rotation.npy')
    np.save(rotationpath, R)
    translatepath = os.path.join(ATLAS_PATH, f'atlas2{animal}.translation.npy')
    np.save(translatepath, t)


    print(f'resolution: {sql_controller.scan_run.resolution}')
    print(f'width: {sql_controller.scan_run.width}')
    print(f'height: {sql_controller.scan_run.height}')
    box_w = sql_controller.scan_run.width * sql_controller.scan_run.resolution / 32  # 10 mum scale
    box_h = sql_controller.scan_run.height * sql_controller.scan_run.resolution / 32  # 10 mum scale
    box_z = sql_controller.get_section_count(animal)  # 20 mum scale

    atlasV7_volume = np.zeros((int(box_h), int(box_w), int(box_z)), dtype=np.uint8)
    print('Shape of atlas volume', atlasV7_volume.shape)
    debug = True
    for structure, (source_point, volume) in sorted(atlas_centers.items()):
        print(str(structure).ljust(7),end=": ")
        results = (R @ source_point.T + t.T) # transform to fit
        #results = np.linalg.inv(output_scale) @ results
        print(results)
        continue
        x = results[0][0] * resolution # new x
        y = results[0][1] * resolution # new y
        z = results[0][2] # z
        x = x - volume.shape[0]/2
        y = y - volume.shape[1]/2
        x_start = int( round(x))
        y_start = int( round(y))
        z_start = int(z - volume.shape[2]/4)

        x_end = int( round(x_start + volume.shape[0]))
        y_end = int( round(y_start + volume.shape[1]))
        z_end = int( round(z_start + (volume.shape[2] + 1) // 2))

        if debug:
            #print('volume shape', volume.shape, end=" ")
            print('COM row',
                  str(int(y)).rjust(4),
                  'mid col',
                  str(int(x)).rjust(4),
                  'mid z',
                  str(int(z)).rjust(4),
                  end=" ")
            print('Row range',
                  str(y_start).rjust(4),
                  str(y_end).rjust(4),
                  'col range',
                  str(x_start).rjust(4),
                  str(x_end).rjust(4),
                  'z range',
                  str(z_start).rjust(4),
                  str(z_end).rjust(4),
                  end=" ")

        if structure in output_centers.keys():
            origin, _ = source_centers[structure]
            xo, yo, zo = origin
            print('COM off by:',
                  round(x - xo, 2),
                  round(y - yo, 2),
                  round(z - zo, 2),
                  end=" ")

        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume.astype(np.uint8)
        volume = volume[:, :, z_indices]
        volume = np.swapaxes(volume, 0, 1)
        try:
            atlasV7_volume[y_start:y_end, x_start:x_end, z_start:z_end] += volume
        except ValueError as ve:
            print('Bad fit', end=" ")

        print()

    print('Shape of downsampled atlas volume', atlasV7_volume.shape)

    print('Resolution at', resolution)

    if create:
        atlasV7_volume = np.rot90(atlasV7_volume, axes=(0, 1))
        atlasV7_volume = np.fliplr(atlasV7_volume)
        atlasV7_volume = np.flipud(atlasV7_volume)
        atlasV7_volume = np.fliplr(atlasV7_volume)

        offset = [0,0,0]
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

