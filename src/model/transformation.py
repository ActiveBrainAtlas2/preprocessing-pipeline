from .atlas_model import Base, AtlasModel
from sqlalchemy import Column, String, Integer,LargeBinary,ForeignKey,DateTime

class Transformation(Base, AtlasModel):
    __tablename__ = 'transformation'
    id =  Column(Integer, primary_key=True, nullable=False)
    source = Column(String,ForeignKey('animal.prep_id'),nullable=False,default=1)
    destination = Column(String,ForeignKey('animal.prep_id'),nullable=False,default=1)
    transformation = Column(LargeBinary,nullable=False)
    transformation_type = Column(Integer,nullable=False)
    updated = Column(DateTime,nullable=False)
    