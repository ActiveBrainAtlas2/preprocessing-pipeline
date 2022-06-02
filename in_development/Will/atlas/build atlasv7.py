
import numpy as np
import os
from abakit.atlas.Atlas import Atlas
from abakit.lib.SqlController import SqlController
from scipy.ndimage.measurements import center_of_mass
from abakit.atlas.NgSegmentMaker import NgConverter
from skimage.filters import gaussian
from abakit.atlas.Assembler import Assembler,get_v7_volume_and_origin

controller = SqlController('DK39')
atlas = Atlas(atlas = 'atlasV7')
atlas.get_com_array()
assembler = Assembler(check=False,side = '_R')
assembler.volumes,assembler.origins = get_v7_volume_and_origin(side = '_R')
assembler.sqlController = atlas.sqlController
assembler.structures = list(assembler.volumes.keys())
assembler.assemble_all_structure_volume()
segment_properties = atlas.get_segment_properties()
folder_name = f'atlas_ogR'
output_dir = os.path.join(atlas.path.segmentation_layer,folder_name)
maker = NgConverter(volume = assembler.combined_volume,scales = [10000,10000,20000])
maker.create_neuroglancer_files(output_dir,segment_properties)