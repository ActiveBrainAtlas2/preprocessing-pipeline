from sqlalchemy import Column, Integer, String, ForeignKey

from database_model.atlas_model import Base, AtlasModel

class Log(Base, AtlasModel):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True)
    prep_id = Column(String)
    level = Column(String)
    logger = Column(String)
    msg = Column(String)
