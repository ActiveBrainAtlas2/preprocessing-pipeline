from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, Float
from .atlas_model import Base, AtlasModel
from model.brain_region import BrainRegion



class AnnotationPoint(Base):
    __tablename__ = 'annotations_points'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, nullable=False)
    FK_input_id = Column(Integer)
    FK_owner_id = Column(Integer)
    FK_structure_id = Column(Integer, ForeignKey('structure.id'), nullable=True)
    label = Column(String, nullable=False)
    segment_id = Column(String, nullable=True)
    ordering = Column(Integer, nullable=False, default=0)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
<<<<<<< HEAD
    active = Column(Boolean, default=True, nullable=False)

=======
    ordering = Column(Integer)
>>>>>>> e90accce200cc9b2d02fba44124401f8312b0c58
    brain_region = relationship('BrainRegion', lazy=True)





