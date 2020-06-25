from datetime import datetime

import yaml
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Date, Boolean, TIMESTAMP, String, Enum, ForeignKey, Float, DateTime, func, \
    Table, create_engine
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class AtlasModel(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    __table_args__ = {'mysql_engine': 'InnoDB'}
    __mapper_args__ = {'always_refresh': True}

    created = Column(TIMESTAMP)
    active = Column(Boolean, default=True, nullable=False)


class AlcAnimal(Base, AtlasModel):
    __tablename__ = 'animal'

    prep_id = Column(String(255), nullable=False, primary_key=True)
    performance_center = Column(Enum("CSHL", "Salk", "UCSD", "HHMI", "Duke"))
    date_of_birth = Column(Date)
    species = Column(Enum("mouse", "rat"))
    strain = Column(String(255))
    sex = Column(Enum("M", "F"))
    genotype = Column(String(255))
    breeder_line = Column(String(255))
    vender = Column(String(255))
    stock_number = Column(String(255))
    tissue_source = Column(String(255))
    ship_date = Column(Date)
    shipper = Column(Enum("FedEx", "UPS"))
    tracking_number = Column(String(255))
    aliases_1 = Column(String(255))
    aliases_2 = Column(String(255))
    aliases_3 = Column(String(255))
    aliases_4 = Column(String(255))
    aliases_5 = Column(String(255))
    comments = Column(String(255))

    scan_runs = relationship('AlcScanRun', backref="animal")
    # histology = relationship(Histology, uselist=False, backref="animal")


class AlcOrganicLabel(Base, AtlasModel):
    __tablename__ = 'organic_label'

    id = Column(Integer, primary_key=True, nullable=False)
    label_id = Column(String(255), nullable=False)
    label_type = Column(
        Enum("Cascade Blue", "Chicago Blue", "Alexa405", "Alexa488", "Alexa647", "Cy2", "Cy3", "Cy5", "Cy5.5", "Cy7",
             "Fluorescein", "Rhodamine B", "Rhodamine 6G", "Texas Red", "TMR"))
    type_lot_number = Column(String(255))
    type_tracer = Column(Enum("BDA", "Dextran", "FluoroGold", "DiI", "DiO"))
    type_details = Column(String(255))
    concentration = Column(Float, default=0)
    excitation_1p_wavelength = Column(Integer, default=0)
    excitation_1p_range = Column(Integer, default=0)
    excitation_2p_wavelength = Column(Integer, default=0)
    excitation_2p_range = Column(Integer, default=0)
    lp_dichroic_cut = Column(Integer, default=0)
    emission_wavelength = Column(Integer, default=0)
    emission_range = Column(Integer, default=0)
    label_source = Column(Enum("", "Invitrogen", "Sigma", "Thermo-Fisher"))
    souce_details = Column(String(255))
    comments = Column(String(255))


injection_virus = Table('injection_virus', Base.metadata,
                        Column('injection_id', Integer, ForeignKey('injection.id'), nullable=False),
                        Column('virus_id', Integer, ForeignKey('virus.id'), nullable=False))


class AlcVirus(Base, AtlasModel):
    __tablename__ = 'virus'

    id = Column(Integer, primary_key=True, nullable=False)
    virus_name = Column(String(255))
    virus_type = Column(
        Enum("Adenovirus", "AAV", "CAV", "DG rabies", "G-pseudo-Lenti", "Herpes", "Lenti", "N2C rabies", "Sinbis"))
    active = Column(Enum("yes", "no"))
    type_details = Column(String(255))
    titer = Column(Float, default=0)
    lot_number = Column(String(255))
    label = Column(Enum("YFP", "GFP", "RFP", "histo-tag"))
    label2 = Column(String(255))
    excitation_1p_wavelength = Column(Integer, default=0)
    excitation_1p_range = Column(Integer, default=0)
    excitation_2p_wavelength = Column(Integer, default=0)
    excitation_2p_range = Column(Integer, default=0)
    lp_dichroic_cut = Column(Integer, default=0)
    emission_wavelength = Column(Integer, default=0)
    emission_range = Column(Integer, default=0)
    virus_source = Column(Enum("Adgene", "Salk", "Penn", "UNC"))
    source_details = Column(String(255))
    comments = Column(String(255))


class AlcInjection(Base, AtlasModel):
    __tablename__ = 'injection'

    id = Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String(255), ForeignKey('animal.prep_id'), nullable=False)
    label_id = Column(Integer, ForeignKey('organic_label.id'))
    performance_center = Column(Enum("CSHL", "Salk", "UCSD", "HHMI", "Duke"))
    anesthesia = Column(Enum("ketamine", "isoflurane"))
    method = Column(Enum("iontophoresis", "pressure", "volume"))
    injection_volume = Column(Float, default=0)
    pipet = Column(Enum("glass", "quartz", "Hamilton", "syringe needle"))
    location = Column(String(255))
    angle = Column(String(255))
    brain_location_dv = Column(Float, default=0)
    brain_location_ml = Column(Float, default=0)
    brain_location_ap = Column(Float, default=0)
    injection_date = Column(Date)
    transport_days = Column(Integer, default=0)
    virus_count = Column(Integer, default=0)

    viruses = relationship("AlcVirus", secondary=injection_virus)


class AlcHistology(Base, AtlasModel):
    __tablename__ = 'histology'

    id = Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String(255), ForeignKey('animal.prep_id'), nullable=False, unique=True)
    virus_id = Column(Integer, ForeignKey('virus.id'), nullable=True)
    label_id = Column(Integer, ForeignKey('organic_label.id'), nullable=True)
    performance_center = Column(Enum("CSHL", "Salk", "UCSD", "HHMI"))
    anesthesia = Column(Enum("ketamine", "isoflurane", "pentobarbital", "fatal plus"))
    perfusion_age_in_days = Column(Integer, nullable=False)
    perfusion_date = Column(Date)
    exsangination_method = Column(Enum("PBS", "aCSF", "Ringers"))
    fixative_method = Column(Enum("Para", "Glut", "Post fix"))
    special_perfusion_notes = Column(String(255))
    post_fixation_period = Column(Integer, default=0, nullable=False)
    whole_brain = Column(Enum("Y", "N"))
    block = Column(String(255))
    date_sectioned = Column(Date)
    sectioning_method = Column(Enum("cryoJane", "cryostat", "vibratome", "optical", "sliding microtiome"))
    section_thickness = Column(Integer, default=20, nullable=False)
    orientation = Column(Enum("coronal", "horizontal", "sagittal", "oblique"))
    oblique_notes = Column(String(255))
    mounting = Column(Enum("every section", "2nd", "3rd", "4th", "5ft", "6th"))
    counterstain = Column(Enum("thionin", "NtB", "NtFR", "DAPI", "Giemsa", "Syto41"))
    comments = Column(String(255))


class AlcScanRun(Base, AtlasModel):
    __tablename__ = 'scan_run'

    id = Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String(255), ForeignKey('animal.prep_id'), nullable=False)
    performance_center = Column(Enum("CSHL", "Salk", "UCSD", "HHMI"))
    machine = Column(Enum("Zeiss", "Axioscan", "Nanozoomer", "Olympus VA"))
    objective = Column(Enum("60X", "40X", "20X", "10X"))
    resolution = Column(Float, default=0)
    number_of_slides = Column(Integer, default=0)
    scan_date = Column(Date)
    file_type = Column(Enum("CZI", "JPEG2000", "NDPI", "NGR"))
    scenes_per_slide = Column(Enum("1", "2", "3", "4", "5", "6"))
    section_schema = Column(Enum("L to R", "R to L"))
    channels_per_scene = Column(Enum("1", "2", "3", "4"))
    slide_folder_path = Column(String(255))
    converted_folder_path = Column(String(255))
    converted_status = Column(Enum("not started", "converted", "converting", "error"))
    ch_1_filter_set = Column(Enum("68", "47", "38", "46", "63", "64", "50"))
    ch_2_filter_set = Column(Enum("68", "47", "38", "46", "63", "64", "50"))
    ch_3_filter_set = Column(Enum("68", "47", "38", "46", "63", "64", "50"))
    ch_4_filter_set = Column(Enum("68", "47", "38", "46", "63", "64", "50"))
    comments = Column(String(255))

    slides = relationship('AlcSlide', lazy=True)


class AlcSlide(Base, AtlasModel):
    __tablename__ = 'slide'

    id = Column(Integer, primary_key=True, nullable=False)
    scan_run_id = Column(Integer, ForeignKey('scan_run.id'))
    slide_physical_id = Column(Integer)
    rescan_number = Column(Enum("1", "2", "3"), default="1", nullable=False)
    slide_status = Column(Enum("Bad", "Good"), nullable=False)
    scenes = Column(Integer, nullable=False)
    insert_before_one = Column(Integer, default=0)
    scene_qc_1 = Column(Integer, default=0)
    insert_between_one_two = Column(Integer, default=0)
    scene_qc_2 = Column(Integer, default=0)
    insert_between_two_three = Column(Integer, default=0)
    scene_qc_3 = Column(Integer, default=0)
    insert_between_three_four = Column(Integer, default=0)
    scene_qc_4 = Column(Integer, default=0)
    insert_between_four_five = Column(Integer, default=0)
    scene_qc_5 = Column(Integer, default=0)
    insert_between_five_six = Column(Integer, default=0)
    scene_qc_6 = Column(Integer, default=0)
    processed = Column(Boolean(), default=False)
    file_size = Column(Float, nullable=False)
    file_name = Column(String(255), nullable=False)
    comments = Column(String(255))

    slide_czi_tifs = relationship('AlcSlideCziTif', lazy=True)


class AlcSlideCziTif(Base, AtlasModel):
    __tablename__ = 'slide_czi_to_tif'

    id = Column(Integer, primary_key=True, nullable=False)
    slide_id = Column(Integer, ForeignKey('slide.id'), nullable=False)
    scene_number = Column(Integer)
    channel = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    file_name = Column(String(255))
    file_size = Column(Float)
    comments = Column(String(255))
    channel_index = Column(Integer)
    scene_index = Column(Integer)
    processing_duration = Column(Float, nullable=False)


class AlcRawSection(Base, AtlasModel):
    __tablename__ = 'raw_section'

    id = Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String(255), ForeignKey('animal.prep_id'), nullable=False)
    section_number = Column(Integer, nullable=False)
    tif_id = Column(Integer, nullable=False)
    slide_physical_id = Column(Integer, nullable=False)
    scene_number = Column(Integer, nullable=False)
    channel = Column(Integer, nullable=False)
    source_file = Column(String(255), nullable=False)
    destination_file = Column(String(255), nullable=False)
    file_status = Column(Enum('unusable', 'blurry', 'good'), nullable=False, default='good')


class ProgressLookup(Base, AtlasModel):
    __tablename__ = 'progress_lookup'

    id = Column(Integer, primary_key=True, nullable=False)
    ordinal = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)
    original_step = Column(String(255), nullable=True)
    category = Column(String(255), nullable=False)
    script = Column(String(255), nullable=True)


class Task(Base, AtlasModel):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True, nullable=False)
    prep_id = Column(String(255), ForeignKey('animal.prep_id'), nullable=False)
    lookup_id = Column(Integer, ForeignKey('progress_lookup.id'), nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    start_date = Column(DateTime(), server_default=func.now())
    end_date = Column(DateTime())

    def __init__(self, prep_id, lookup_id, completed):
        now = datetime.now()
        self.prep_id = prep_id
        self.lookup_id = lookup_id
        self.completed = completed
        self.start_date = now
        self.end_date = now
        self.created = now
