import sys
from pathlib import Path

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from brain_structure_manager import BrainStructureManager
from library.controller.structure_com_controller import StructureCOMController
from library.controller.annotation_session_controller import AnnotationSessionController
from library.database_model.annotation_points import PolygonSequence




def create_foundation_brain_polygon_sequences(animal):
    brainManager = BrainStructureManager(animal)
    brainManager.load_aligned_contours()
    contours = brainManager.aligned_contours
    annotationSessionController = AnnotationSessionController(animal)
    structureController = StructureCOMController(animal)
    xy_resolution = brainManager.sqlController.scan_run.resolution
    zresolution = brainManager.sqlController.scan_run.zresolution
    source = 'NA'
    for abbreviation, v in contours.items():
        FK_brain_region_id = structureController.structure_abbreviation_to_id(abbreviation=abbreviation)
        FK_session_id = annotationSessionController.create_annotation_session(annotation_type='POLYGON_SEQUENCE', 
                                                                                FK_user_id=1, FK_prep_id=animal, FK_brain_region_id=FK_brain_region_id)
        for section, vertices in v.items():
            polygon_index = int(section)
            point_order = 1
            z = float(int(section) * zresolution)
            vlist = []
            for x,y in vertices:
                x = x * 32 * xy_resolution
                y = y * 32 * xy_resolution
                #print(source, x, y, z, polygon_index, point_order, FK_session_id)
                polygon_sequence = PolygonSequence(x=x, y=y, z=z, source=source, 
                                                polygon_index=polygon_index, point_order=point_order, FK_session_id=FK_session_id)
                point_order += 1
                vlist.append(polygon_sequence)
                #brainManager.sqlController.add_row(polygon_sequence)
            brainManager.sqlController.session.bulk_save_objects(vlist)
            brainManager.sqlController.session.commit()


if __name__ == '__main__':
    animals = ['MD585', 'MD589', 'MD594']
    for animal in animals:
        create_foundation_brain_polygon_sequences(animal)
