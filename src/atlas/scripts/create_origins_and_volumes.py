import os

from foundation_contour_aligner import FoundationContourAligner
from brain_structure_manager import BrainStructureManager

def create_contours(animal):
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
    brainManager.save_atlas_origins_and_volumes_and_meshes()

def create_brain_origins_volumes(animal):
    brainManager = BrainStructureManager(animal)
    brainManager.load_aligned_contours()
    brainManager.compute_origins_and_volumes_for_all_segments()
    #brainManager.save_coms()
    print(f'Length {animal} origins={len(brainManager.origins)}')
    print(f'Length {animal} volumes={len(brainManager.volumes)}')
    print(f'Length {animal} structures={len(brainManager.structures)}')
    #brainManager.load_data([brainManager])
    brainManager.save_brain_origins_and_volumes_and_meshes()

def test_brain_origins(animal):
    """
    SC thumbnail_aligned should be x=760, y=350, z=128
    SC thumbnail should be x=590, y=220, z=128
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


if __name__ == '__main__':
    animals = ['MD585', 'MD589', 'MD594']
    """
    for animal in animals:
        print(f'Working on {animal}')
        create_contours(animal)
        create_brain_origins_volumes(animal)
    """
    create_brain_origins_volumes('MD589')
    #create_atlas_origins_volumes()
    #test_brain_origins('MD589')
