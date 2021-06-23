from sqlalchemy import Column, String
from .atlas_model import AtlasModel, Base


class User(Base, AtlasModel):
    __tablename__ = 'auth_user'
    id = Column(String, nullable=False, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)