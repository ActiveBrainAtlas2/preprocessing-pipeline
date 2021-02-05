import os, sys
import shutil
from pathlib import Path
import argparse
import numpy as np
import tifffile as tiff
import neuroglancer
from tqdm import tqdm
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager


def create_mesh(animal, limit, chunk, debug):
    scale = 3
    fileLocationManager = FileLocationManager(animal)
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/thumbnail_aligned')
    """you might want to change the output dir"""
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, f'mesh_chunk_{chunk}')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    midfile = tiff.imread(midfilepath)
    height, width = midfile.shape

    ## take a sample from the middle of the stack
    if limit > 0:
        files = files[midpoint-limit:midpoint+limit]

    resolution = 1000
    scales = (resolution*scale, resolution*scale, resolution*scale)
    chunk_size = [chunk, chunk, chunk]
    volume_size = (width, height, len(files))
    data_type = np.uint8
    volume = np.zeros((volume_size), dtype=data_type)

    voxel_size = scales

    json_descriptor = '{{"fragments": ["mesh.{}.{}"]}}'

    img_path = Path(INPUT)

    mesh_list = []
    for f in tqdm(files):
        filepath = os.path.join(INPUT, f)
        img = tiff.imread(filepath)
        mesh_list.append(img)
    mesh = np.dstack(mesh_list)
    mesh = np.transpose(mesh, (2, 0, 1))

    ids = [int(i) for i in np.unique(midfile[:])]

    dims = neuroglancer.CoordinateSpace(
        names=['x', 'y', 'z'],
        units=['nm', 'nm', 'nm'],
        scales=scales)

    vol = neuroglancer.LocalVolume(
        data=mesh,
        dimensions=dims
    )

    img_path.parent.joinpath(
        'output', 'mesh').mkdir(exist_ok=True, parents=True)

    for ID in ids[1:]:
        print(ID)
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
    parser.add_argument('--limit', help='Enter the # of files to test', required=False, default=0)
    parser.add_argument('--chunk', help='Enter the chunk size', required=True)
    parser.add_argument('--debug', help='debug?', required=True)
    args = parser.parse_args()
    animal = args.animal
    limit = int(args.limit)
    chunk = int(args.chunk)
    debug = bool({'true': True, 'false': False}[args.debug.lower()])
    create_mesh(animal, limit, chunk, debug)

