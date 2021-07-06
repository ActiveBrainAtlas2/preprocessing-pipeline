from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .atlas_model import Base, AtlasModel
from .slide_czi_to_tif import SlideCziTif


class Slide(Base, AtlasModel):
    __tablename__ = 'slide'

    id =  Column(Integer, primary_key=True, nullable=False)
    scan_run_id = Column(Integer, ForeignKey('scan_run.id'))
    slide_physical_id = Column(Integer)
    rescan_number = Column(Enum("1", "2", "3"), default="1", nullable=False)
    slide_status = Column(Enum("Bad", "Good"), nullable=False)
    scenes = Column(Integer, nullable=False)
    insert_before_one = Column(Integer, default=0)
    scene_qc_1 =  Column(Integer, default=0)
    insert_between_one_two =  Column(Integer, default=0)
    scene_qc_2 =  Column(Integer, default=0)
    insert_between_two_three = Column(Integer, default=0)
    scene_qc_3 =  Column(Integer, default=0)
    insert_between_three_four =  Column(Integer, default=0)
    scene_qc_4 =  Column(Integer, default=0)
    insert_between_four_five =  Column(Integer, default=0)
    scene_qc_5 = Column(Integer, default=0)
    insert_between_five_six = Column(Integer, default=0)
    scene_qc_6 =  Column(Integer, default=0)
    processed = Column(Boolean(), default=False)
    file_size = Column(Float, nullable=False)
    file_name = Column(String, nullable=False)
    comments = Column(String)

    slide_czi_tifs = relationship('SlideCziTif', lazy=True)
