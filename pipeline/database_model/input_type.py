from sqlalchemy import Column, String
from database_model.atlas_model import AtlasModel, Base


class ComType(Base, AtlasModel):
    __tablename__ = 'input_type'
    id = Column(String, nullable=False, primary_key=True)
    input_type = Column(String, nullable=False)