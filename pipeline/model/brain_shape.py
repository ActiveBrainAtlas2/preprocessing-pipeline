from sqlalchemy import Boolean, Column, String, Integer, Float, ForeignKey
from sqlalchemy.sql.sqltypes import LargeBinary

from model.atlas_model import Base, AtlasModel

class BrainShape(Base, AtlasModel):
    __tablename__ = 'brain_shape'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)    
    FK_structure_id = Column(Integer, ForeignKey('structure.id'), nullable=True)
    dimensions = Column(String, nullable=False)
    xoffset = Column(Float, nullable=False)
    yoffset = Column(Float, nullable=False)
    zoffset = Column(Float, nullable=False)
    transformed = Column(Boolean, nullable=False, default=True)
    numpy_data = Column(LargeBinary)




