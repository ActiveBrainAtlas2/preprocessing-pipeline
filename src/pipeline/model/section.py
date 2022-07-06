from inspect import getargs
from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
# from abakit.model.slide_czi_to_tif import SlideCziTif
from abakit.model.atlas_model import Base, AtlasModel
# from abakit.model.slide import Slide

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
    slide_id = Column(Integer, ForeignKey('slide.id'), nullable=False)
    slide_czi_tif = relationship("slide_czi_tif", back_populates="section")

    def get_rotation(self):
        return getattr(self.slide,f'scene_rotation_{self.scene_number}')






