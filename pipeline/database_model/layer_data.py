from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.sql.sqltypes import Float

from database_model.atlas_model import Base, AtlasModel

class LayerData(Base, AtlasModel):
    __tablename__ = 'layer_data'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, nullable=False)
    input_type_id = Column(Integer)
    person_id = Column(Integer)
    structure_id = Column(Integer, ForeignKey('structure.id'), nullable=True)
    layer = Column(String, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    section = Column(Float, nullable=False)
    updated = Column(TIMESTAMP)

    structure = relationship('Structure', lazy=True)





