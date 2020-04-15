from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from .atlas_model import Base, AtlasModel


class Section(Base, AtlasModel):
    __tablename__ = 'section'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)
    file_name = Column(String, nullable=False)
    section_number = Column(Integer, nullable=False)
    tif_id = Column(Integer, nullable=False)
    slide_physical_id = Column(Integer, nullable=False)
    scene_number = Column(Integer, nullable=False)
    section_qc = Column(Enum('OK','Replaced'), nullable=False, default='OK')
    ch_1_path =  Column(String)
    ch_2_path =  Column(String)
    ch_3_path =  Column(String)
    ch_4_path =  Column(String)


class RawSection(Base, AtlasModel):
    __tablename__ = 'raw_section'
    id =  Column(Integer, primary_key=True, nullable=False)

    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)
    section_number = Column(Integer, nullable=False)
    tif_id = Column(Integer, nullable=False)
    slide_physical_id = Column(Integer, nullable=False)
    scene_number = Column(Integer, nullable=False)
    channel = Column(Integer, nullable=False)
    source_file = Column(String, nullable=False)
    destination_file = Column(String, nullable=False)
    file_status = Column(Enum('unusable', 'blurry', 'good'), nullable=False, default='good')


