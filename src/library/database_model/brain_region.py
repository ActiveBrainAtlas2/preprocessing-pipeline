from sqlalchemy import Column, String, Integer, DateTime

from library.database_model.atlas_model import Base, AtlasModel

class BrainRegion(Base, AtlasModel):
    __tablename__ = 'brain_region'
    __table_args__ = {'extend_existing': True}
    id =  Column(Integer, primary_key=True, nullable=False)
    abbreviation = Column(String, nullable=False)
    description = Column(String, nullable=False)
    active =  Column(Integer,default=1)
    created =  Column(DateTime)




