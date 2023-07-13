"""
This script will take a source brain (where the data comes from) and an image brain 
(the brain whose images you want to display unstriped) and align the data from the point brain
to the image brain. It first aligns the point brain data to the atlas, then that data
to the image brain. It prints out the data by default and also will insert
into the database if given a layer name.
"""
from library.image_manipulation.filelocation_manager import data_path
from library.utilities.atlas import volume_to_polygon, save_mesh
from library.utilities.atlas import singular_structures, symmetricalize_volume
import os
import sys
import numpy as np
from collections import defaultdict
from pathlib import Path
from skimage.filters import gaussian

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())


class BrainMerger():

    def __init__(self):
        self.symmetry_list = singular_structures
        self.volumes_to_merge = defaultdict(list)
        self.origins_to_merge = defaultdict(list)
        atlas = 'atlasV8'
        self.data_path = os.path.join(data_path, 'atlas_data', atlas)
        self.volume_path = os.path.join(self.data_path, 'structure')
        self.origin_path = os.path.join(self.data_path, 'origin')
        self.mesh_path = os.path.join(self.data_path, 'mesh')
        self.volumes = {}
        self.margin = 25
        self.threshold = 0.25  # the closer to zero, the bigger the structures
        # a value of 0.01 results in very big close fitting structures

    def pad_volume(self, size, volume):
        size_difference = size - volume.shape
        xr, yr, zr = ((size_difference)/2).astype(int)
        xl, yl, zl = size_difference - np.array([xr, yr, zr])
        return np.pad(volume, [[xl, xr], [yl, yr], [zl, zr]])

    def get_merged_landmark_probability(self, structure, volumes):
        force_symmetry = (structure in self.symmetry_list)
        lvolumes = len(volumes)
        if lvolumes == 1:
            print(f'{structure} has only one volume')
            return volumes[0]
        elif lvolumes > 1:
            sizes = np.array([vi.shape for vi in volumes])
            volume_size = sizes.max(0) + self.margin
            volumes = [self.pad_volume(volume_size, vi) for vi in volumes]
            volumes = list([(v > 0).astype(np.int32) for v in volumes])

            merged_volume = np.sum(volumes, axis=0)
            merged_volume_prob = merged_volume / float(np.max(merged_volume))
            if force_symmetry:
                merged_volume_prob = symmetricalize_volume(merged_volume_prob)

            # increasing the STD makes the volume smoother
            # Smooth the probability
            average_volume = gaussian(merged_volume_prob, 3.0)
            color = 1
            average_volume[average_volume > self.threshold] = color
            average_volume[average_volume != color] = 0
            average_volume = average_volume.astype(np.uint8)
            return average_volume
        else:
            print(f'{structure} has no volumes to merge')
            return None

    def save_atlas_origins_and_volumes_and_meshes(self):
        """Saves everything to disk
        """
        os.makedirs(self.origin_path, exist_ok=True)
        os.makedirs(self.volume_path, exist_ok=True)
        os.makedirs(self.mesh_path, exist_ok=True)

        origins = {structure: np.mean(
            origin, axis=0) for structure, origin in self.origins_to_merge.items()}
        for structure in self.volumes.keys():
            x, y, z = origins[structure]
            volume = self.volumes[structure]
            origin_array = np.array(list(origins.values()))
            centered_origin = (x, y, z) - origin_array.mean(0)
            aligned_structure = volume_to_polygon(
                volume=volume, origin=centered_origin, times_to_simplify=3)
            origin_filepath = os.path.join(
                self.origin_path, f'{structure}.txt')
            volume_filepath = os.path.join(
                self.volume_path, f'{structure}.npy')
            mesh_filepath = os.path.join(self.mesh_path, f'{structure}.stl')
            if 'SC' in structure:
                print(origin_filepath)
                print(volume_filepath)
                print(mesh_filepath)
            np.savetxt(origin_filepath, (x, y, z))
            np.save(volume_filepath, volume)
            save_mesh(aligned_structure, mesh_filepath)
