from sqlalchemy import Column, String, Integer, LargeBinary, ForeignKey, DateTime

from database_model.animal import Animal
from database_model.atlas_model import Base, AtlasModel


class Transformation(Base, AtlasModel):
    __tablename__ = 'transformation'
    id = Column(Integer, primary_key=True, nullable=False)
    source = Column(String, ForeignKey(Animal.prep_id), nullable=False,)
    destination = Column(String, ForeignKey(Animal.prep_id), nullable=False)
    transformation = Column(LargeBinary, nullable=False)
    transformation_type = Column(Integer, nullable=False)
    updated = Column(DateTime, nullable=False)
