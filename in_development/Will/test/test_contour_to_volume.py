import json
from abakit.lib.Controllers.UrlController import UrlController
from abakit.lib.annotation_layer import AnnotationLayer
from abakit.lib.Brain import Brain
from abakit.atlas.VolumeMaker import VolumeMaker
# from abakit.atlas.NgSegmentMaker import NgConverter
import os
import numpy as np
import json

import cv2
from django.template import Origin
import numpy as np
from sympy import interpolate
from tqdm import tqdm
from scipy.ndimage.measurements import center_of_mass

"""
William, this is the last script for creating the atlas

This will create a precomputed volume of the Active Brain Atlas which
you can import into neuroglancer
"""
import os
import numpy as np
from timeit import default_timer as timer
import shutil
from cloudvolume import CloudVolume
from abakit.atlas.Atlas import Atlas
from abakit.lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer
from abakit.atlas.Assembler import AtlasAssembler, BrainAssembler
from abakit.atlas.BrainStructureManager import BrainStructureManager

class NgConverter(NumpyToNeuroglancer):
    def __init__(self, volume = None, scales =None, offset=[0, 0, 0], layer_type='segmentation'):
        self.volume = np.pad(volume,[[1,0],[1,0],[1,0]])
        self.scales = scales
        self.offset = offset
        self.layer_type = layer_type
        self.precomputed_vol = None

    def init_precomputed(self, path):
        info = CloudVolume.create_new_info(
            num_channels = self.volume.shape[3] if len(self.volume.shape) > 3 else 1,
            layer_type = self.layer_type,
            data_type = str(self.volume.dtype),  # Channel images might be 'uint8'
            encoding = 'raw',                    # raw, jpeg, compressed_segmentation, fpzip, kempressed
            resolution = self.scales,            # Voxel scaling, units are in nanometers
            voxel_offset = self.offset -np.array([1,1,1]),          # x,y,z offset in voxels from the origin
            chunk_size = [64,64,64],           # units are voxels
            volume_size = self.volume.shape[:3], # e.g. a cubic millimeter dataset
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=True, progress=True)
        self.precomputed_vol.commit_info()
        self.precomputed_vol[:, :, :] = self.volume

    def create_neuroglancer_files(self,output_dir,segment_properties):
        self.reset_output_path(output_dir)
        self.init_precomputed(output_dir)
        self.add_segment_properties(segment_properties)
        self.add_downsampled_volumes()
        self.add_segmentation_mesh()
    
    def reset_output_path(self,output_dir):
        if os.path.exists(output_dir):
            print(output_dir)
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
            
class NgSegmentMaker(NgConverter):
    def __init__(self, debug = False,out_folder = 'atlas_test',*arg,**kwarg):
        NgConverter.__init__(self,*arg,**kwarg)
        self.OUTPUT_DIR = os.path.join(self.path.segmentation_layer,out_folder)
        self.debug = debug

    def get_atlas_resolution(self):
        self.fixed_brain = BrainStructureManager('MD589')
        resolution = self.fixed_brain.get_resolution()
        SCALE = 32
        return int(resolution * SCALE * 1000)
    
    def get_animal_resolution(self):
        resolution = self.get_resolution()
        return int(resolution * self.DOWNSAMPLE_FACTOR * 1000)

class AtlasNgMaker(Atlas,NgSegmentMaker):
    def __init__(self,atlas_name,debug = False,out_folder = 'atlas_test',threshold = 0.9,sigma = 3.0,offset = None):
        Atlas.__init__(self,atlas_name)
        NgSegmentMaker.__init__(self, debug,out_folder=out_folder,offset=offset)
        self.assembler = AtlasAssembler(atlas_name, threshold=threshold,sigma = sigma)
        self.resolution = self.get_atlas_resolution()
    
    def create_atlas_neuroglancer(self):
        self.volume = self.assembler.combined_volume
        self.scales = [self.resolution,self.resolution,20]
        segment_properties = self.get_segment_properties()
        self.create_neuroglancer_files(self.OUTPUT_DIR,segment_properties)

class BrainNgMaker(BrainStructureManager,NgSegmentMaker):
    def __init__(self,animal,debug = False,out_folder = 'animal_folder', *args, **kwargs):
        BrainStructureManager.__init__(self,animal)
        NgSegmentMaker.__init__(self, debug,out_folder=out_folder, *args, **kwargs)
        self.assembler = BrainAssembler(animal)
        self.resolution = self.get_animal_resolution()
    
    def create_brain_neuroglancer(self):
        self.volume = self.assembler.combined_volume
        self.scales = [self.resolution,self.resolution,20]
        segment_properties = self.get_segment_properties()
        self.create_neuroglancer_files(self.OUTPUT_DIR,segment_properties)

if __name__ == '__main__':
    atlas = 'atlasV8'
    debug = False
    maker = AtlasNgMaker(atlas,debug,threshold=0.9,out_folder = 'new_atlas',sigma = 3.0)
    maker.assembler.assemble_all_structure_volume()
    maker.create_atlas_neuroglancer()

volume_id = '2b9c285bdf34b5df5378b572748da0512238ab31'
controller = UrlController()
url = controller.get_urlModel(312)
state_json = json.loads(url.url)
layers = state_json['layers']
for layeri in layers:
    if layeri['type'] == 'annotation':
        layer = AnnotationLayer(layeri)
        volume = layer.get_annotation_with_id(volume_id)
        if volume is not None:
            break

vmaker = VolumeMaker()
structure,contours = volume.get_volume_name_and_contours()
vmaker.set_aligned_contours({structure:contours})
vmaker.compute_origins_and_volumes_for_all_segments(interpolate=1)
res = [0.325,0.325,20]
segment_properties = [(1,'structure')]
folder_name = f'test'
path = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/structures'
output_dir = os.path.join(path,folder_name)
maker = NgConverter(volume = vmaker.volumes[structure].astype(np.uint8),scales = [res*1000,res*1000,20000],offset=list(vmaker.origins[structure]))
maker.create_neuroglancer_files(output_dir,segment_properties=[(1,structure)])
print(output_dir)