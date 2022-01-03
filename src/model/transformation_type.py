from .atlas_model import Base, AtlasModel
from sqlalchemy import Column, String, Integer,LargeBinary,ForeignKey

class TransformationType(Base, AtlasModel):
    __tablename__ = 'transformation_type'
    id =  Column(Integer, primary_key=True, nullable=False)
    transformation_type = Column(String,nullable=False)