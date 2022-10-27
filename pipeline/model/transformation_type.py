from sqlalchemy import Column, String, Integer

from model.atlas_model import Base, AtlasModel

class TransformationType(Base, AtlasModel):
    __tablename__ = 'transformation_type'
    id =  Column(Integer, primary_key=True, nullable=False)
    transformation_type = Column(String,nullable=False)