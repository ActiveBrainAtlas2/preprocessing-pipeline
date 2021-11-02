from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, TIMESTAMP
from .atlas_model import Base, AtlasModel



class UrlModel(Base, AtlasModel):
    __tablename__ = 'neuroglancer_urls'
    id =  Column(Integer, primary_key=True, nullable=False)
    url = Column(String, nullable=False)
    person_id = Column(Integer, nullable=False)
    vetted = Column(Boolean, default=False, nullable=False)
    updated = Column(TIMESTAMP)
    comments = Column(String)





