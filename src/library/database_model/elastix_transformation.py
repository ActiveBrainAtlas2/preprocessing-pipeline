from sqlalchemy import Column, String, Integer, Float

from library.database_model.atlas_model import Base, AtlasModel

class ElastixTransformation(Base, AtlasModel):
    """This class is responsible for storing the rigid transforamtion
    parameters. It also contains a column for storing how well
    the fixed image aligns with the moving image.
    """
    
    __tablename__ = 'elastix_transformation'
    id =  Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String, nullable=False)
    section = Column(String, nullable=False)
    rotation = Column(Float, nullable=False)
    xshift = Column(Float, nullable=False)
    yshift = Column(Float, nullable=False)
    metric = Column(Float, nullable=False, default=0)
    iteration = Column(Integer, nullable=False, default=0)




