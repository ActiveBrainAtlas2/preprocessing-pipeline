"""
This is the first script run in the pipeline process.
It goes through the czi directory and gets the biggest
4 files with the bioformats tool: showinf. It then
populates the database with this meta information. The user
then validates the data with the ActiveAtlasAdmin database portal
"""
import os, sys
import argparse
from pathlib import Path
from pprint import pprint
PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())
from utilities.file_location import FileLocationManager
from utilities.utilities_bioformats import get_czi_metadata, get_fullres_series_indices


def test_czi(animal, czi_file):
    """
    Scans the czi dir to extract the meta information for each tif file
    Args:
        animal: the animal as primary key

    Returns: nothing
    """

    fileLocationManager = FileLocationManager(animal)


    # Get metadata from the czi file
    czi_file_path = os.path.join(fileLocationManager.czi, czi_file)
    metadata_dict = get_czi_metadata(czi_file_path)
    pprint(metadata_dict)

    print()
    series = get_fullres_series_indices(metadata_dict)

    for j, series_index in enumerate(series):
        scene_number = j + 1
        channels = range(metadata_dict[series_index]['channels'])
        #print('channels range and dict', channels,metadata_dict[series_index]['channels'])
        channel_counter = 0
        width = metadata_dict[series_index]['width']
        height = metadata_dict[series_index]['height']
        for channel in channels:
            channel_counter += 1
            newtif = '{}_S{}_C{}.tif'.format(czi_file, scene_number, channel_counter)
            newtif = newtif.replace('.czi', '').replace('__','_')
            print(f'file:{newtif} width={width}, height={height}')


if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on CZI')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    parser.add_argument('--filepath', help='Enter the filepath of the czi', required=True)
    args = parser.parse_args()
    animal = args.animal
    filepath = args.filepath
    test_czi(animal, filepath)
