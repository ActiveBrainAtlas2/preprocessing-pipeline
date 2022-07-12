from .atlas_model import Base, AtlasModel
from sqlalchemy import Column, String, Integer,LargeBinary,ForeignKey,DateTime
from sqlalchemy.orm import relationship
from abakit.model.animal import Animal
class Transformation(Base, AtlasModel):
    __tablename__ = 'transformation'
    id =  Column(Integer, primary_key=True, nullable=False)
    source = Column(String,ForeignKey(Animal.prep_id),nullable=False,)
    destination = Column(String,ForeignKey(Animal.prep_id),nullable=False)
    transformation = Column(LargeBinary,nullable=False)
    transformation_type = Column(Integer,nullable=False)
    updated = Column(DateTime,nullable=False)
    