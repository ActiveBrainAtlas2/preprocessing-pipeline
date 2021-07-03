from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from .atlas_model import Base, AtlasModel
from .section import Section
#from .slide import Slide



class SlideCziTif(Base, AtlasModel):
    __tablename__ = 'slide_czi_to_tif'

    id =  Column(Integer, primary_key=True, nullable=False)
    slide_id = Column(Integer, ForeignKey('slide.id'), nullable=False)
    file_name = Column(String, nullable=False)
    scene_number = Column(Integer, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Float)
    comments = Column(String)
    channel = Column(Integer)
    scene_index = Column(Integer)
    processing_duration = Column(Float, nullable=False)

    #slide = relationship("Slide", back_populates="slide_czi_tifs")
    #slide = relationship("Slide")
    section = relationship("Section", uselist=False, back_populates="slide_czi_tif")
