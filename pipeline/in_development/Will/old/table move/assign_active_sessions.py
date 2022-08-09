import enum
from pipeline.Controllers.SqlController import SqlController
from model.annotation_points import AnnotationPoint,MarkedCell,PolygonSequence,StructureCOM,COMSources,PolygonSources,CellSources
from model.annotation_points import AnnotationSession,AnnotationType
import numpy as np
controller = SqlController('DK55')

sessions = controller.session.query(AnnotationSession).all()
ids = [i.id for i in sessions]
types = [i.annotation_type for i in sessions]

for i in range(len(sessions)):
    id = ids[i]
    type = types[i]
    session = sessions[i]
    if type ==AnnotationType.MARKED_CELL:
        if bool(controller.session.query(MarkedCell).filter(MarkedCell.FK_session_id==id).first()):
            session.active=1
            controller.update_row(session)
    if type ==AnnotationType.POLYGON_SEQUENCE:
        if bool(controller.session.query(PolygonSequence).filter(PolygonSequence.FK_session_id==id).first()):
            session.active=1
            controller.update_row(session)
    if type ==AnnotationType.STRUCTURE_COM:
        if bool(controller.session.query(StructureCOM).filter(StructureCOM.FK_session_id==id).first()):
            session.active=1
            controller.update_row(session)

# def parse_data(rows):
#     session_id = [i.FK_session_id for i in rows]
#     unique_ids = np.unique(session_id)
#     for id in unique_ids:
#         session = controller.session.query(AnnotationSession).get(id)
#         sessions.append(session)

# polygons = controller.session.query(PolygonSequence).all()
# coms = controller.session.query(StructureCOM).all()
# # parse_data(cells)
# parse_data(polygons)
# parse_data(coms)
# for sessioni in sessions:
#     sessioni.active = 1
# controller.session.commit()
print()