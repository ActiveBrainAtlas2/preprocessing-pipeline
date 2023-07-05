import os
import numpy as np
from skimage.filters import gaussian

from foundation_contour_aligner import FoundationContourAligner
from brain_structure_manager import BrainStructureManager
from brain_merger import BrainMerger
from library.utilities.atlas import save_mesh, volume_to_polygon
from library.utilities.utilities_mask import normalize8

def create_foundation_brain_contours(animal):
    aligner = FoundationContourAligner(animal)
    if os.path.exists(aligner.aligned_and_padded_contour_path):
        print(f'{aligner.aligned_and_padded_contour_path} already exists.')
        return
    aligner.load_contours_for_foundation_brains()
    aligner.create_clean_transform()
    aligner.load_transformation_to_align_contours()
    aligner.align_contours()
    aligner.save_json_contours()



def create_atlas_origins_volumes():
    fixed_brain = 'MD589'
    brainManager = BrainStructureManager(fixed_brain)
    brainManager.fixed_brain = BrainStructureManager(fixed_brain)
    brainManager.moving_brains = [BrainStructureManager('MD585'), BrainStructureManager('MD594')]
    brainManager.load_aligned_contours()
    brainManager.compute_origins_and_volumes_for_all_segments()
    #brainManager.save_coms()
    print(f'Length atlas origins={len(brainManager.origins)}')
    print(f'Length atlas volumes={len(brainManager.volumes)}')
    print(f'Length atlas structures={len(brainManager.structures)}')
    brainManager.load_data([brainManager.fixed_brain]+brainManager.moving_brains)
    brainManager.load_data_from_fixed_and_moving_brains()
    brainMerger = BrainMerger()
    for structure in brainManager.volumes_to_merge:
        volumes = brainManager.volumes_to_merge[structure]
        volume = brainMerger.get_merged_landmark_probability(structure, volumes)
        brainManager.volumes[structure]= volume

    brainManager.save_atlas_origins_and_volumes_and_meshes()

def create_foundation_brain_origins_volumes(animal):
    brainManager = BrainStructureManager(animal)
    brainManager.load_aligned_contours()
    brainManager.compute_origins_and_volumes_for_all_segments()
    #brainManager.save_coms()
    print(f'Length {animal} origins={len(brainManager.origins)}')
    print(f'Length {animal} volumes={len(brainManager.volumes)}')
    print(f'Length {animal} structures={len(brainManager.structures)}')
    #brainManager.load_data([brainManager])
    brainManager.save_brain_origins_and_volumes_and_meshes()

def pad_volume(size, volume):
    size_difference = size - volume.shape
    xr,yr,zr = ((size_difference)/2).astype(int)
    xl,yl,zl = size_difference - np.array([xr,yr,zr])
    return np.pad(volume,[[xl,xr],[yl,yr],[zl,zr]])


def test_brain_origins(animal):
    """
    SC thumbnail_aligned should be x=760, y=350, z=128
    SC thumbnail should be x=590, y=220, z=128
    """
    atlas_path = '/net/birdstore/Active_Atlas_Data/data_root/atlas_data'
    sc1_path = os.path.join(atlas_path, 'MD585', 'structure', 'SC.npy')
    sc2_path = os.path.join(atlas_path, 'MD589', 'structure', 'SC.npy')
    sc3_path = os.path.join(atlas_path, 'MD594', 'structure', 'SC.npy')
    sc1 = np.load(sc1_path)
    sc2 = np.load(sc2_path)
    sc3 = np.load(sc3_path)
    volume_list = [sc1, sc2, sc3]
    sizes = np.array([vi.shape for vi in volume_list])
    print(f'sizes={sizes}')
    margin = 50
    volume_size = sizes.max(0) + margin
    print(f'volume size={volume_size}')
    volumes = [pad_volume(volume_size, vi) for vi in volume_list]
    volumes = list([(v > 0).astype(np.int32) for v in volumes])
    #volumes = self.refine_align_volumes(volumes)

    merged_volume = np.sum(volumes, axis=0)
    merged_volume_prob = merged_volume / float(np.max(merged_volume))
    # increasing the STD makes the volume smoother
    average_volume = gaussian(merged_volume_prob, 5.0) # Smooth the probability
    print(f'merged volume dtype={merged_volume.dtype} shape={merged_volume.shape}')
    print(f'gaussed volume dtype={average_volume.dtype} shape={average_volume.shape}')
    average_volume[average_volume > 0.5] = 100
    average_volume[average_volume != 100] = 0
    average_volume = average_volume.astype(np.uint8)
    ids, counts = np.unique(average_volume, return_counts=True)
    print(f'average volume dtype={average_volume.dtype} shape={average_volume.shape}')
    print(ids)
    print(counts)
    mesh_filepath = os.path.join(atlas_path,'atlasV8/structure', 'SC.npy')
    np.save(mesh_filepath, average_volume)







    """
    brainManager = BrainStructureManager(animal)
    brainManager.load_aligned_contours()
    brainManager.test_origins_and_volumes_for_all_segments()
    aligner = FoundationContourAligner(animal)
    if not os.path.exists(aligner.aligned_and_padded_contour_path):
        print(f'{aligner.aligned_and_padded_contour_path} does not exists.')
        return
    aligner.load_contours_for_foundation_brains()
    vertices = aligner.contour_per_structure_per_section['SC'][128]
    for vertex in sorted(vertices):
        print(vertex[0]/32, vertex[1]/32)
    print()
    aligner.create_clean_transform()
    print(aligner.section_offsets[128])
    """


if __name__ == '__main__':
    animals = ['MD585', 'MD589', 'MD594']

       
    for animal in animals:
        print(f'Working on {animal}')
        continue
        create_foundation_brain_contours(animal)
        create_foundation_brain_origins_volumes(animal)
    
    #create_brain_origins_volumes('MD589')
    create_atlas_origins_volumes()
    #test_brain_origins('MD589')
