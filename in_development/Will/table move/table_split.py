import enum
from abakit.lib.Controllers.SqlController import SqlController
from abakit.model.annotation_points import AnnotationPoint,MarkedCell,PolygonSequence,StructureCOM,COMSources,PolygonSources,CellSources
from abakit.model.annotation_points import AnnotationSession,AnnotationType
from abakit.model.brain_region import BrainRegion
from abakit.model.cell_type import CellType
import numpy as np
import pandas as pd
def move_coms():
    controller = SqlController('DK55')
    points = controller.session.query(AnnotationPoint).filter(AnnotationPoint.label=="COM").filter(AnnotationPoint.active==1).all()
    prep_ids = [i.prep_id for i in points]
    structure = [i.FK_structure_id for i in points]
    coords = [[i.x,i.y,i.z] for i in points]
    data = pd.DataFrame(dict(prep_ids=prep_ids,structure = structure,coords=coords,points=points))
    for prepi in data.prep_ids.unique():
        is_prepi = data.prep_ids==prepi
        prepi_data =data[is_prepi]
        assert len(prepi_data.structure.unique())==len(prepi_data)
        for _,row in prepi_data.iterrows():
            com = row.points
            session = AnnotationSession(FK_prep_id = com.prep_id,FK_parent=0,FK_annotator_id=com.FK_owner_id,FK_structure_id = com.FK_structure_id,annotation_type = AnnotationType.STRUCTURE_COM)
            controller.add_row(session)
            com_data = StructureCOM( x=com.x, y=com.y, z=com.z,source=COMSources.MANUAL,FK_session_id=session.id)
            controller.add_row(com_data)

def clean_up_coms():
    to_numpy = lambda x : np.array([np.array(i) for i in x.to_numpy()])
    controller = SqlController('DK55')
    points = controller.session.query(AnnotationPoint).filter(AnnotationPoint.label=="COM").filter(AnnotationPoint.active==1).all()
    prep_ids = [i.prep_id for i in points]
    structure = [i.FK_structure_id for i in points]
    coords = [[i.x,i.y,i.z] for i in points]
    data = pd.DataFrame(dict(prep_ids=prep_ids,structure = structure,coords=coords,points=points))
    for prepi in data.prep_ids.unique():
        is_prepi = data.prep_ids==prepi
        prepi_data =data[is_prepi]
        if len(prepi_data.structure.unique())!=len(prepi_data):
            structure_counts = prepi_data.structure.value_counts()
            for str_id,count in structure_counts.items():
                if count>1:
                    def delete_rows(prepi_stri_data,id_of_the_one):
                        i = 0
                        for point_id, pointi in prepi_stri_data.iterrows():
                            if not i == id_of_the_one:
                                db_point_id = pointi.points.id
                                controller.session.query(AnnotationPoint).filter(AnnotationPoint.id == db_point_id).delete()
                                controller.session.commit()
                            i+=1
                    prepi_stri_data = prepi_data[prepi_data.structure==str_id]
                    coord_counts = prepi_stri_data.coords.value_counts()
                    more_than_one = np.array(coord_counts.values)>1
                    if np.sum(more_than_one)==1:
                        id_of_the_one = np.where(more_than_one)[0][0]
                        delete_rows(prepi_stri_data,id_of_the_one)
                    elif len(coord_counts.keys()) == 2 and np.all(np.isclose(coord_counts.keys()[0],coord_counts.keys()[1],atol=10)):
                        delete_rows(prepi_stri_data,id_of_the_one=0)
                    else:
                        print(prepi,str_id)
                        print(coord_counts)
                        raise NotImplementedError
            ...

def move_polygons():
    controller = SqlController('DK55')
    get_structure = lambda structurei:controller.session.query(BrainRegion).filter(BrainRegion.abbreviation==structurei).first()
    structure_exists = lambda structurei:bool(get_structure(structurei))
    points = controller.session.query(AnnotationPoint).filter(AnnotationPoint.FK_structure_id==54).filter(AnnotationPoint.active==1).all()
    data = {}
    data['prep_ids'] = [i.prep_id for i in points]
    data['label'] = [i.label for i in points]
    data['coords'] = [[i.x,i.y,i.z] for i in points]
    data['ordering'] = [i.ordering for i in points]
    data['polygon_id'] = [i.polygon_id for i in points]
    data['volume_id'] = [i.volume_id for i in points]
    data['owner_id'] = [i.FK_owner_id for i in points]
    data['point'] = [i for i in points]
    data = pd.DataFrame(data)
    objects=[]
    for prepi in data.prep_ids.unique():
        print(prepi)
        prep_data = data[data.prep_ids==prepi]
        for structurei in prep_data.label.unique():
            if structure_exists(structurei):
                print(structurei)
                structure_data = prep_data[prep_data.label==structurei]
                assert structure_data.owner_id.unique().size==1
                owner = structure_data.owner_id.unique()[0]
                structure = get_structure(structurei)
                session = AnnotationSession(FK_prep_id = prepi,FK_parent=0,FK_annotator_id=owner,FK_structure_id = structure.id,annotation_type = AnnotationType.POLYGON_SEQUENCE)
                controller.add_row(session)
                sections = [i[2] for _,i in structure_data['coords'].iteritems()]
                unique_sections = np.unique(sections)
                sections_sort_id = np.argsort(unique_sections)
                section_to_polygon_index = dict(zip(unique_sections,sections_sort_id))
                for _,row in structure_data.iterrows():
                    row = row.point
                    polygon_index=section_to_polygon_index[row.z]
                    polygon_data = PolygonSequence( x=row.x, y=row.y, z=row.z,source=PolygonSources.NA,FK_session_id=session.id,point_order = row.ordering,polygon_index=polygon_index)
                    objects.append(polygon_data)
        controller.session.bulk_save_objects(objects)
        controller.session.commit()

def move_manual_cells():
    include = ['starter','premotor','trigeminal premotor','Premotor V','V premotor','Premotor','Starter','Mcherry','Trigeminal premotor','Starter cell','Mcherry only']
    def label_to_category(label): 
        premotor=['premotor','trigeminal premotor','Premotor V','V premotor','Premotor','Trigeminal premotor']
        starter=['starter','Starter','Starter cell']
        Mcherry=['Mcherry','Mcherry only']
        if label in starter:
            return 2 
        elif label in premotor: 
            return 1 
        elif label in Mcherry:
            return 3 
    def get_structure_id_of_point(pointi):
        trigeminal = ['trigeminal premotor','Trigeminal premotor']
        str_5N_L = ['Premotor V','V premotor']
        if pointi.label in trigeminal:
            return 57
        if pointi.label in str_5N_L:
            return 8
        else:
            return 52
    controller = SqlController('DK55')
    points = controller.session.query(AnnotationPoint).filter(AnnotationPoint.FK_structure_id==52).all()
    points = [i for i in points if i.label in include]
    data = {}
    data['prep_ids'] = [i.prep_id for i in points]
    data['label'] = [label_to_category(i.label) for i in points]
    data['coords'] = [[i.x,i.y,i.z] for i in points]
    data['owner_id'] = [i.FK_owner_id for i in points]
    data['structure_id'] = [get_structure_id_of_point(i) for i in points]
    data['point'] = [i for i in points]
    data = pd.DataFrame(data)
    objects = []
    for prepi in data.prep_ids.unique():
        prep_data = data[data.prep_ids==prepi]
        for structurei in prep_data.structure_id.unique():
            structure_data = prep_data[data.structure_id==structurei]
            for owner in structure_data.owner_id.unique():
                owner_data = structure_data[data.owner_id==owner]
                for labeli in owner_data.label.unique():
                    print(prepi,structurei,owner,labeli)
                    label_data = owner_data[owner_data.label==labeli]
                    session = AnnotationSession(FK_prep_id = prepi,FK_parent=0,FK_annotator_id=owner,FK_structure_id = structurei,annotation_type = AnnotationType.MARKED_CELL)
                    controller.add_row(session)
                    for _,row in label_data.iterrows():
                        row = row.point
                        polygon_data = MarkedCell(x=row.x, y=row.y, z=row.z,source=CellSources.HUMAN_POSITIVE,FK_session_id=session.id,FK_cell_type_id=labeli)
                        objects.append(polygon_data)
    controller.session.bulk_save_objects(objects)
    controller.session.commit()

def move_detected_cells():
    include = ['positive_round1','negative_round1','detected_soma_round2_unsure','detected_soma_round2_sure','negative annotation','positive annotation','unsure annotation1','sure annotation','samick_cell_detection','detected_soma_multi_level']
    def label_to_category(label): 
        human_positive=['positive_round1','negative annotation',]
        human_negative=['negative_round1','positive annotation',]
        machine_sure=['detected_soma_round2_sure','sure annotation','samick_cell_detection','detected_soma_multi_level']
        machine_unsure=['detected_soma_round2_unsure','unsure annotation1',]
        if label in human_positive:
            return CellSources.HUMAN_POSITIVE
        elif label in human_negative: 
            return CellSources.HUMAN_NEGATIVE
        elif label in machine_sure:
            return CellSources.MACHINE_SURE         
        elif label in machine_unsure:
            return CellSources.MACHINE_UNSURE 
    def label_to_cell_type(label): 
        round0=['negative annotation','positive annotation','unsure annotation1','sure annotation',]
        round1=['positive_round1','negative_round1',]
        round2=['detected_soma_round2_unsure','detected_soma_round2_sure',]
        round3=['detected_soma_multi_level']
        samick=['samick_cell_detection',]
        if label in round0:
            return 4
        elif label in round1: 
            return 5
        elif label in round2:
            return 6   
        elif label in round3:
            return 7
        elif label in samick:
            return 8
    controller = SqlController('DK55')
    points = controller.session.query(AnnotationPoint).filter(AnnotationPoint.FK_structure_id==52).all()
    points = [i for i in points if i.label in include]
    data = {}
    data['prep_ids'] = [i.prep_id for i in points]
    data['label'] = [i.label for i in points]
    data['source'] = [label_to_category(i) for i in data['label']]
    data['cell_type'] = [label_to_cell_type(i) for i in data['label']]
    data['coords'] = [[i.x,i.y,i.z] for i in points]
    data['owner_id'] = [i.FK_owner_id for i in points]
    data['point'] = [i for i in points]
    data = pd.DataFrame(data)
    objects = []
    for prepi in data.prep_ids.unique():
        prep_data = data[data.prep_ids==prepi]
        for owner in prep_data.owner_id.unique():
            owner_data = prep_data[data.owner_id==owner]
            for sourcei in owner_data.source.unique():
                label_data = owner_data[owner_data.source==sourcei]
                for cell_type in label_data.cell_type.unique():
                    print(prepi,owner,sourcei,cell_type)
                    cell_type_data = label_data[label_data.cell_type==cell_type]
                    session = AnnotationSession(FK_prep_id = prepi,FK_parent=0,FK_annotator_id=owner,FK_structure_id = 52,annotation_type = AnnotationType.MARKED_CELL)
                    controller.add_row(session)
                    for _,row in cell_type_data.iterrows():
                        row = row.point
                        polygon_data = MarkedCell(x=row.x, y=row.y, z=row.z,source=sourcei,FK_session_id=session.id,FK_cell_type_id=cell_type)
                        objects.append(polygon_data)
    controller.session.bulk_save_objects(objects)
    controller.session.commit()

# move_manual_cells()
move_polygons()

print()