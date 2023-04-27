from sqlalchemy import Column, String, Date, Enum
from sqlalchemy.orm import relationship

from library.database_model.atlas_model import AtlasModel, Base
from library.database_model.scan_run import ScanRun


class Animal(Base, AtlasModel):
    """This is the main model used by almost all the other models in the entire project.
    It includes the fields originally set by David and Yoav.
    """

    __tablename__ = 'animal'
    
    prep_id = Column(String, nullable=False, primary_key=True)
    #performance_center = Column(Enum("CSHL", "Salk", "UCSD", "HHMI", "Duke"))
    date_of_birth = Column(Date)
    species = Column(Enum("mouse", "rat"))
    strain = Column(String)
    sex = Column(Enum("M", "F"))
    genotype = Column(String)
    vender = Column(String)
    stock_number = Column(String)
    tissue_source = Column(String)
    ship_date = Column(Date)
    shipper = Column(Enum("FedEx", "UPS"))
    tracking_number = Column(String)
    alias = Column(String)
    comments = Column(String)
    scan_runs = relationship(ScanRun, backref="animal")