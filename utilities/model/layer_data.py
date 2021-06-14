from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, TIMESTAMP
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.sqltypes import Float
from .atlas_model import Base, AtlasModel



class LayerData(Base, AtlasModel):
    __tablename__ = 'layer_data'
    id =  Column(Integer, primary_key=True, nullable=False)
    url_id = Column(Integer, nullable=False)
    prep_id = Column(String, nullable=False)
    input_type_id = Column(Integer)
    person_id = Column(Integer)
    structure_id = Column(Integer, ForeignKey('structure.id'), nullable=True)
    layer = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    section = Column(Float, nullable=False)
    segment_id = Column(Integer)
    updated = Column(TIMESTAMP)

    structure = relationship('Structure', lazy=True)





