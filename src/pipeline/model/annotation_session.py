
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey,Enum
from sqlalchemy.sql.sqltypes import Float
from abakit.model.atlas_model import Base
from abakit.model.brain_region import BrainRegion
from abakit.model.user import User
import enum

class AnnotationType(enum.Enum):
    POLYGON_SEQUENCE = 'POLYGON_SEQUENCE'
    MARKED_CELL = 'MARKED_CELL'
    STRUCTURE_COM = 'STRUCTURE_COM'

class AnnotationSession(Base):
    __tablename__ = 'annotation_session'
    id =  Column(Integer, primary_key=True, nullable=False)
    FK_prep_id = Column(String, nullable=False)
    FK_parent = Column(Integer)
    FK_annotator_id = Column(Integer, ForeignKey('auth_user.id'), nullable=True)
    FK_structure_id = Column(Integer, ForeignKey('structure.id'), nullable=True)
    annotation_type = Column(Enum(AnnotationType))    
    brain_region = relationship('BrainRegion', lazy=True)
    user = relationship('User', lazy=True)
    active =  Column(Integer)

