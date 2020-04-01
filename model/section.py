from sqlalchemy import Column, String, Integer, ForeignKey
from .atlas_model import Base, AtlasModel



class RawSection(Base, AtlasModel):
    __tablename__ = 'raw_sections'
    id =  Column(Integer, primary_key=True, nullable=False)

    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)
    section_number = Column(Integer, nullable=False)
    file_name = Column(String, nullable=False)

