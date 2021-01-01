"""
This will create a precomputed volume of the Active Brain Atlas which
you can import into neuroglancer
"""
import argparse
import sys
import numpy as np
from pathlib import Path

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())
from utilities_cvat_neuroglancer import get_structure_number, NumpyToNeuroglancer, get_segment_properties
RESOLUTION = 0.325
OUTPUT_DIR = '../atlas_ng/'

def create_atlas():

    # unzip your structure and origin zip files in this path, or create your own path
    #atlas_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/atlas_data/atlasV7')
    atlas_dir = Path('/net/birdstore/Active_Atlas_Data/copied_from_S3/mousebrainatlas-data/CSHL_volumes/atlasV7/atlasV7_10.0um_scoreVolume/score_volumes')
    origin_dir = atlas_dir / 'origin'
    volume_dir = atlas_dir / 'structure'

    structure_volume_origin = {}
    for origin_file, volume_file in zip(sorted(origin_dir.iterdir()), sorted(volume_dir.iterdir())):
        assert origin_file.stem == volume_file.stem
        structure = origin_file.stem

        color = get_structure_number(structure.replace('_L', '').replace('_R', ''))

        origin = np.loadtxt(origin_file)
        volume = np.load(volume_file)

        volume = np.rot90(volume, axes=(0, 1))
        volume = np.flip(volume, axis=0)
        volume[volume > 0.80] = color
        volume = volume.astype(np.uint8)

        structure_volume_origin[structure] = (volume, origin)

    col_length = 1000
    row_length = 1000
    z_length = 300
    atlasV7_volume = np.zeros(( int(row_length), int(col_length), z_length), dtype=np.uint8)

    for structure, (volume, origin) in sorted(structure_volume_origin.items()):
        print(str(structure).ljust(7),end=": ")
        x, y, z = origin
        x_start = int( round(x + col_length / 2))
        y_start = int( round(y + row_length / 2))
        z_start = int(z) // 2 + z_length // 2
        x_end = x_start + volume.shape[0]
        y_end = y_start + volume.shape[1]
        z_end = z_start + (volume.shape[2] + 1) // 2

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


        z_indices = [z for z in range(volume.shape[2]) if z % 2 == 0]
        volume = volume[:, :, z_indices]
        volume = np.swapaxes(volume, 0, 1)

        try:
            atlasV7_volume[y_start:y_end, x_start:x_end, z_start:z_end] += volume
        except ValueError as ve:
            print(ve, end=" ")

        print()

    scale = (10/0.325)

    atlasV7_volume = np.rot90(atlasV7_volume, axes=(0, 1))
    atlasV7_volume = np.fliplr(atlasV7_volume)
    atlasV7_volume = np.flipud(atlasV7_volume)
    atlasV7_volume = np.fliplr(atlasV7_volume)


    offset = [0,0,0]
    RESOLUTION = int(0.325 * 1000 * scale)
    ng = NumpyToNeuroglancer(atlasV7_volume, [RESOLUTION, RESOLUTION, 20000], offset=offset)
    ng.init_precomputed(OUTPUT_DIR)
    ng.add_segment_properties(get_segment_properties())
    ng.add_downsampled_volumes()
    ng.add_segmentation_mesh()





if __name__ == '__main__':
    create_atlas()

