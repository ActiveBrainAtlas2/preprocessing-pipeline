
import numpy as np
import os
from atlas.atlas_manager import Atlas
from pipeline.Controllers.SqlController import SqlController
from atlas.NgSegmentMaker import NgConverter
from atlas.Assembler import Assembler,get_v7_volume_and_origin,get_assembled_atlas_v7

controller = SqlController('DK39')
atlas = Atlas(atlas = 'atlasV7')
atlas.get_com_array()
assembler = Assembler(check=False,side = '_R')
assembler.volumes,assembler.origins = get_v7_volume_and_origin()
assembler.sqlController = atlas.sqlController
assembler.structures = list(assembler.volumes.keys())
segment_to_id = controller.get_segment_to_id_where_segment_are_brain_regions()
assembler.assemble_all_structure_volume(segment_to_id)
segment_properties = atlas.get_segment_properties()
folder_name = f'atlas_ogR'
output_dir = os.path.join(atlas.path.segmentation_layer,folder_name)
maker = NgConverter(volume = assembler.combined_volume,scales = [10000,10000,20000])
maker.create_neuroglancer_files(output_dir,segment_properties)