import os
import sys
import numpy as np
from skimage.filters import gaussian

from foundation_contour_aligner import FoundationContourAligner
from brain_structure_manager import BrainStructureManager
from brain_merger import BrainMerger
from library.controller.annotation_session_controller import AnnotationSessionController
from library.controller.structure_com_controller import StructureCOMController
from library.database_model.annotation_points import PolygonSequence

def create_foundation_brain_contours(animal):
    aligner = FoundationContourAligner(animal)
    if os.path.exists(aligner.aligned_and_padded_contour_path):
        print(f'{aligner.aligned_and_padded_contour_path} already exists.')
        return
    aligner.load_csv_for_foundation_brains()
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
    brainManager.compute_origins_and_volumes_for_all_structure_segments()
    brainManager.save_brain_origins_and_volumes_and_meshes()

def test_for_existing_brain_data(animals):
    errors = []
    lengths = set()
    for animal in animals:
        brainManager = BrainStructureManager(animal)
        for p in [os.path.join(brainManager.animal_directory, 'mesh'), 
                  os.path.join(brainManager.animal_directory, 'origin'), os.path.join(brainManager.animal_directory,'structure')]:
            if not os.path.exists(p):
                errors.append(f'{p} does not exist')
            else:
                lengths.add(len(os.listdir(p)))

    if len(lengths) > 1:
        errors.append('The length of the 3 directories are not the same.')
    if len(lengths) > 0:
        l = next(iter(lengths))
        if l < 20:
            errors.append(f'There are only {l} entries in each dir.')

    return errors


def test_for_existing_atlas_data(atlas='atlasV8'):
    errors = []
    lengths = set()
    brainManager = BrainStructureManager(atlas)
    for p in [brainManager.mesh_path, brainManager.origin_path, brainManager.volume_path]:
        if not os.path.exists(p):
            errors.append(f'{p} does not exist')
        else:
            lengths.add(len(os.listdir(p)))
                
    if len(lengths) > 1:
        errors.append('The length of the 3 directories is not the same.')

    if len(lengths) > 0:
        l = next(iter(lengths))
        if l < 20:
            errors.append(f'There are only {l} entries in each dir.')

    return errors


def pad_volume(size, volume):
    size_difference = size - volume.shape
    xr,yr,zr = ((size_difference)/2).astype(int)
    xl,yl,zl = size_difference - np.array([xr,yr,zr])
    return np.pad(volume,[[xl,xr],[yl,yr],[zl,zr]])

def create_foundation_brain_polygon_sequences(animal):
    brainManager = BrainStructureManager(animal)
    brainManager.load_aligned_contours()
    contours = brainManager.aligned_contours
    annotationSessionController = AnnotationSessionController(animal)
    structureController = StructureCOMController(animal)
    xy_resolution = brainManager.sqlController.scan_run.resolution
    zresolution = brainManager.sqlController.scan_run.zresolution
    source = 'NA'
    for abbreviation,v in contours.items():
        FK_brain_region_id = structureController.structure_abbreviation_to_id(abbreviation=abbreviation)
        FK_session_id = annotationSessionController.create_annotation_session(annotation_type='POLYGON_SEQUENCE', 
                                                                                FK_user_id=1, FK_prep_id=animal, FK_brain_region_id=FK_brain_region_id)
        for section, vertices in v.items():
            polygon_index = int(section)
            point_order = 1
            print(type(section))
            z = float(int(section) * zresolution)
            for x,y in vertices:
                x = x * 32 * xy_resolution
                y = y * 32 * xy_resolution
                print(source, x, y, z, polygon_index, point_order, FK_session_id)
                polygon_sequence = PolygonSequence(x=x, y=y, z=z, source=source, 
                                                   polygon_index=polygon_index, point_order=point_order, FK_session_id=FK_session_id)
                point_order += 1
                brainManager.sqlController.add_row(polygon_sequence)

def volume_origin_creation():
    controller = StructureCOMController('MD589')
    sessions = controller.get_active_sessions()
    animal_users = set()
    for session in sessions:
        animal_users.add((session.FK_prep_id, session.FK_user_id))
    animal_users = list(animal_users)
    for animal_user in animal_users:
        animal = animal_user[0]
        annotator_id = animal_user[1]
        if 'test' in animal or 'Atlas' in animal:
            continue
        print(animal, annotator_id)
        continue
        brainManager = BrainStructureManager(animal)
        brainManager.compute_origin_and_volume_for_brain_structures(animal, annotator_id=annotator_id)



def test_brain_origins(animal):
    """
    SC thumbnail_aligned should be x=760, y=350, z=128
    SC thumbnail should be x=590, y=220, z=128
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
    contours = brainManager.aligned_contours
    annotationSessionController = AnnotationSessionController(animal)
    structureController = StructureCOMController(animal)
    xy_resolution = brainManager.sqlController.scan_run.resolution
    zresolution = brainManager.sqlController.scan_run.zresolution
    source = 'NA'
    xs = []
    ys = []
    zs = []
    for abbreviation,v in contours.items():
        if 'VLL_R' in abbreviation:
            FK_brain_region_id = structureController.structure_abbreviation_to_id(abbreviation=abbreviation)
            FK_session_id = annotationSessionController.create_annotation_session(annotation_type='POLYGON_SEQUENCE', 
                                                                                    FK_user_id=1, FK_prep_id=animal, FK_brain_region_id=FK_brain_region_id)
            for section, vertices in v.items():
                polygon_index = int(section)
                point_order = 1
                print(type(section))
                z = float(int(section) * zresolution)
                for x,y in vertices:
                    x = x * 32 * xy_resolution
                    y = y * 32 * xy_resolution
                    xs.append(x)
                    ys.append(y)
                    zs.append(z)
                    print(animal, abbreviation, source, x, y, z, polygon_index, point_order, FK_session_id)
                    point_order += 1
    print(np.mean(xs), np.mean(ys), np.mean(zs))
    """
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

           
    """
    for animal in animals:
        print(f'Working on {animal}')
        create_foundation_brain_contours(animal)
        errors = test_for_existing_brain_data(animals)
        if len(errors) > 0:
            for error in errors:
                print(error)
            create_foundation_brain_origins_volumes(animal)
        else:
            print('All foundation brain mesh,origin and volumes exist.')
    errors = test_for_existing_atlas_data(atlas='atlasV8')
    if len(errors) > 0:
        for error in errors:
            print(error)
        create_atlas_origins_volumes()
    else:
        print('All atlas mesh,origin and volume data exist.')
   
    for animal in animals:
        test_brain_origins(animal)
    """
    #create_foundation_brain_contours('MD585')
    #create_foundation_brain_origins_volumes('MD585')
    volume_origin_creation()
    """
    for animal in animals:
        create_foundation_brain_polygon_sequences(animal)
    """