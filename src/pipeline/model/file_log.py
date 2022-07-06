from datetime import datetime

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, ForeignKey
from .atlas_model import Base, AtlasModel



class FileLog(Base, AtlasModel):
    __tablename__ = 'file_log'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, ForeignKey('animal.prep_id'), nullable=False)
    progress_id = Column(String, ForeignKey('progress_lookup.id'), nullable=False)
    filename = Column(String, nullable=False)

    animal = relationship("Animal")
    # progress = relationship("Progress")



