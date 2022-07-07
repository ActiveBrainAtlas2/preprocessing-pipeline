from sqlalchemy import Column, String, Integer, Float
from .atlas_model import Base, AtlasModel

class ElastixTransformation(Base, AtlasModel):
    __tablename__ = 'elastix_transformation'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, nullable=False)
    section = Column(String, nullable=False)
    rotation = Column(Float, nullable=False)
    xshift = Column(Float, nullable=False)
    yshift = Column(Float, nullable=False)




