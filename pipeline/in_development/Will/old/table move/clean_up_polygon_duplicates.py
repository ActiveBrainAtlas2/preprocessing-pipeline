import enum
from pipeline.Controllers.Controller import Controller
from model.annotation_points import AnnotationPoint,MarkedCell,PolygonSequence,StructureCOM,COMSources,PolygonSources,CellSources
from model.annotation_points import AnnotationSession,AnnotationType
import numpy as np
import pandas as pd
controller = Controller()

sessions = controller.session.query(AnnotationSession)\
    .filter(AnnotationSession.active==1)\
    .filter(AnnotationSession.annotation_type==AnnotationType.POLYGON_SEQUENCE).all()
ids = [i.id for i in sessions]

for id in ids:
    volume_points = controller.session.query(PolygonSequence)\
    .filter(PolygonSequence.FK_session_id==id).all()
    volume = {}
    volume['coordinate']=[[i.x,i.y,i.z] for i in volume_points]
    volume['point_ordering']=[i.point_order for i in volume_points]
    volume['polygon_ordering']=[i.polygon_index for i in volume_points]
    volume['point']=[i for i in volume_points]
    volume = pd.DataFrame(volume)
    volume = volume.sort_values('polygon_ordering')
    for polygoni in volume.polygon_ordering.unique():
        polygoni = volume[volume.polygon_ordering==polygoni]
        polygoni.sort_values('point_ordering')
        point_counts = polygoni.point_ordering.value_counts()
        for point_id,count in point_counts.items():
            if count>1:
                def delete_rows(polygon_data,id_of_the_one):
                    i = 0
                    for point_id, pointi in polygon_data.iterrows():
                        if not i == id_of_the_one:
                            pid = pointi.point.id
                            controller.session.query(AnnotationPoint).filter(AnnotationPoint.id == pid).delete()
                            controller.session.commit()
                        i+=1
                polygon_data = polygoni[polygoni.point_ordering==point_id]
                delete_rows(polygon_data,0)
