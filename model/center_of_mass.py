from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Float
from .atlas_model import Base, AtlasModel



class CenterOfMass(Base, AtlasModel):
    __tablename__ = 'center_of_mass'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)
    structure_id = Column(String, ForeignKey('structure.id'), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    section = Column(Integer, nullable=False)
    side = Column(String, nullable=False)




