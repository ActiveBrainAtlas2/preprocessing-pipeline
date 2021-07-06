from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship

from .atlas_model import Base, AtlasModel


class Section(Base, AtlasModel):
    __tablename__ = 'sections'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)
    czi_file = Column(String, nullable=False)
    slide_physical_id = Column(Integer, nullable=False)
    file_name = Column(String, nullable=False)
    tif_id = Column(Integer, ForeignKey('slide_czi_to_tif.id'), nullable=False)
    scene_number = Column(Integer, nullable=False)
    scene_index = Column(Integer, nullable=False)
    channel = Column(Integer, nullable=False)
    channel_index = Column(Integer, nullable=False)

    slide_czi_tif = relationship("SlideCziTif", back_populates="section")





