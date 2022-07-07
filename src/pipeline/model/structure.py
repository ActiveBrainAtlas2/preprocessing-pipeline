from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from .atlas_model import Base, AtlasModel



class Structure(Base, AtlasModel):
    __tablename__ = 'structure'
    id =  Column(Integer, primary_key=True, nullable=False)
    abbreviation = Column(String, nullable=False)
    description = Column(String, nullable=False)
    color = Column(Integer, nullable=False)
    hexadecimal = Column(String, nullable=False)
    is_structure = Column(Integer, nullable=False)




