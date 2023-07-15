import sys
from pathlib import Path

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from brain_structure_manager import BrainStructureManager
from brain_merger import BrainMerger
from library.controller.polygon_sequence_controller import PolygonSequenceController
from library.controller.structure_com_controller import StructureCOMController

def volume_origin_creation():
    structureController = StructureCOMController('MD589')
    polygonController = PolygonSequenceController('MD589')
    sc_sessions = structureController.get_active_sessions()
    pg_sessions = polygonController.get_available_volumes_sessions()
    animal_users = set()
    for session in sc_sessions:
        animal_users.add((session.FK_prep_id, session.FK_user_id))
    for session in pg_sessions:
        animal_users.add((session.FK_prep_id, session.FK_user_id))

    
    animal_users = list(animal_users)
    #animal_users = [['MD585', 1],['MD589', 1], ['MD594', 1]]
    brainMerger = BrainMerger()
    for animal_user in sorted(animal_users):
        animal = animal_user[0]
        annotator_id = animal_user[1]
        if 'test' in animal or 'Atlas' in animal or annotator_id in (3, 34, 37):
            continue
        if annotator_id != 1:
            continue
        brainManager = BrainStructureManager(animal)
        brainManager.annotator_id = annotator_id
        brainManager.fixed_brain = BrainStructureManager('Allen')
        brainManager.fixed_brain.annotator_id = 1
        brainManager.compute_origin_and_volume_for_brain_structures(brainManager, brainMerger, annotator_id=annotator_id)

    for structure in brainMerger.volumes_to_merge:
        volumes = brainMerger.volumes_to_merge[structure]
        origins = brainMerger.volumes_to_merge[structure]
        print(f'{structure} has {len(volumes)} volumes and {len(origins)} origins.')
        
        volume = brainMerger.get_merged_landmark_probability(structure, volumes)
        brainMerger.volumes[structure]= volume

    brainMerger.save_atlas_origins_and_volumes_and_meshes()



if __name__ == '__main__':
    animals = ['MD585', 'MD589', 'MD594']
    volume_origin_creation()
