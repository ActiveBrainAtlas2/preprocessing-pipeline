import enum
from abakit.lib.SqlController import SqlController
from abakit.model.annotation_points import AnnotationPoint,MarkedCell,PolygonSequence,StructureCOM,COMSources,PolygonSources,CellSources
from abakit.model.annotation_session import AnnotationSession,AnnotationType
import numpy as np
controller = SqlController('DK55')

sessions = []

def parse_data(rows):
    session_id = [i.FK_session_id for i in rows]
    unique_ids = np.unique(session_id)
    for id in unique_ids:
        session = controller.session.query(AnnotationSession).get(id)
        sessions.append(session)

# cells = controller.session.query(MarkedCell).all()
polygons = controller.session.query(PolygonSequence).all()
coms = controller.session.query(StructureCOM).all()
# parse_data(cells)
parse_data(polygons)
parse_data(coms)
for sessioni in sessions:
    sessioni.active = 1
controller.session.commit()
print()