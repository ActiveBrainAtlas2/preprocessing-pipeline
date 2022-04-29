import enum
from abakit.lib.SqlController import SqlController
from abakit.model.annotation_points import AnnotationPoint,MarkedCell,PolygonSequence,StructureCOM,COMSources,PolygonSources,CellSources
from abakit.model.annotation_session import AnnotationSession,AnnotationType
from abakit.model.brain_region import BrainRegion
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
move_polygons()
print()