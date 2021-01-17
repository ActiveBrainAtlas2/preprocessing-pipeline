import os
import argparse

import numpy as np
import tifffile as tiff
import neuroglancer
import shutil
from pathlib import Path
from skimage import io
from tqdm import tqdm

from utilities.file_location import FileLocationManager



def create_mesh(animal):

    json_descriptor = '{{"fragments": ["mesh.{}.{}"]}}'
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/thumbnail_aligned')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'shell')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    img_path = Path(OUTPUT_DIR)
    files = sorted(os.listdir(INPUT))
    limit = 150
    midpoint = len(files) // 2
    start = midpoint - limit
    finish = midpoint + limit

    mesh_list = []
    for f in tqdm(files[start:finish]):
        tif = tiff.imread(os.path.join(INPUT, f))
        mesh_list.append(tif)
    mesh = np.dstack(mesh_list)
    mesh = np.transpose(mesh, (2, 0, 1))

    ids = [int(i) for i in np.unique(mesh[:])]

    vol = neuroglancer.LocalVolume(
        data=mesh,
        dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='nm', scales=[10000,10000,1000]),
        voxel_offset=[0,0,0]
    )

    img_path.parent.joinpath(
        'output', 'mesh').mkdir(exist_ok=True, parents=True)

    for ID in ids[1:]:
        print('ID',ID)
        mesh_data = vol.get_object_mesh(ID)
        with open(
                str(img_path.parent / 'output' / 'mesh' / '.'.join(
                    ('mesh', str(ID), str(ID)))), 'wb') as meshfile:
            meshfile.write(mesh_data)
        with open(
                str(img_path.parent / 'output' / 'mesh' / ''.join(
                    (str(ID), ':0'))), 'w') as ff:
            ff.write(json_descriptor.format(ID, ID))

    print('ids to insert into URL:')
    ids_string = '[\'' + '\'_\''.join([str(i) for i in ids[1:]]) + '\']'
    print(ids_string)

    print('done')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    create_mesh(animal)


