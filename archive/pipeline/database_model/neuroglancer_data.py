from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey
from database_model.atlas_model import Base, AtlasModel



class AvailableNeuroglancerData(Base, AtlasModel):
    __tablename__ = 'available_neuroglancer_data'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)
    description = Column(String, nullable=False)
    url = Column(String, nullable=False)

    animal = relationship("Animal")



