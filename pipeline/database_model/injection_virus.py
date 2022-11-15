from sqlalchemy import Column, Integer, ForeignKey, Table

from database_model.atlas_model import Base

injection_virus = Table('injection_virus', Base.metadata,
                        
    Column('injection_id', Integer, ForeignKey('injection.id'), nullable=False),
    Column('virus_id', Integer, ForeignKey('virus.id'), nullable=False),
)