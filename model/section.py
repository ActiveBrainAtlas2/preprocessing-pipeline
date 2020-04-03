from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from .atlas_model import Base, AtlasModel



class RawSection(Base, AtlasModel):
    __tablename__ = 'raw_section'
    id =  Column(Integer, primary_key=True, nullable=False)

    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)
    section_number = Column(Integer, nullable=False)
    source_file = Column(String, nullable=False)
    destination_file = Column(String, nullable=False)
    file_status = Column(Enum('unusable', 'blurry', 'good'), nullable=False, default='good')


