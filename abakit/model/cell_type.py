from sqlalchemy import Column, String, Integer
from .atlas_model import Base, AtlasModel

class CellType(Base, AtlasModel):
    __tablename__ = 'cell_type'
    id =  Column(Integer, primary_key=True, nullable=False)
    cell_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    active = Column(Integer)





