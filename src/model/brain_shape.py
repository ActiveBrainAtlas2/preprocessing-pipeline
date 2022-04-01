from sqlalchemy import Column, String, Integer, ForeignKey
from .atlas_model import Base, AtlasModel
from sqlalchemy.sql.sqltypes import LargeBinary



class BrainShape(Base, AtlasModel):
    __tablename__ = 'brain_shape'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False, unique=True)    
    FK_structure_id = Column(Integer, ForeignKey('structure.id'), nullable=True)
    numpy_data = Column(LargeBinary)




