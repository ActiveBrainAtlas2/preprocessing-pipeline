"""
This is the first script run in the pipeline process.
It goes through the czi directory and gets the biggest
4 files with the bioformats tool: showinf. It then
populates the database with this meta information. The user
then validates the data with the ActiveAtlasAdmin database portal
"""
import argparse
import os
from lib.utilities_bioformats import get_czi_metadata, get_fullres_series_indices

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--czi_file_path', help='Enter the full path to 1 CZI file', required=True)
    args = parser.parse_args()
    czi_file_path = args.czi_file_path
    metadata_dict = get_czi_metadata(czi_file_path)
    print(metadata_dict)
    series = get_fullres_series_indices(metadata_dict)
    print('series', series)
    scenes = len(series)
    print()
    print('# scenes', scenes)

    czi_file = os.path.basename(czi_file_path)
    for j, series_index in enumerate(series):
        scene_number = j + 1
        channels = range(metadata_dict[series_index]['channels'])
        width = metadata_dict[series_index]['width']
        height = metadata_dict[series_index]['height']
        channel_counter = 0
        for channel in channels:
            channel_counter += 1
            newtif = '{}_S{}_C{}.tif'.format(czi_file, scene_number, channel_counter)
            newtif = newtif.replace('.czi', '').replace('__','_')
            print(f'File: {newtif} height: {height}, width {width}, channel {channel}')
            
    