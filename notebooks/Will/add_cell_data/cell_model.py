from sqlalchemy import Column, Integer, String,BigInteger,BLOB,Float
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class Cell(Base):
    __tablename__ = 'features'
    id = Column(BigInteger,primary_key=True)
    prep_id = Column(String)
    section = Column(Integer)
    x = Column(Integer)
    y = Column(Integer)
    cell_images = Column(BLOB)
    DMVec1 = Column(Float)
    DMVec2 = Column(Float)
    DMVec3 = Column(Float)
    DMVec4 = Column(Float)
    DMVec5 = Column(Float)
    DMVec6 = Column(Float)
    DMVec7 = Column(Float)
    DMVec8 = Column(Float)
    DMVec9 = Column(Float)
    DMVec10 = Column(Float)