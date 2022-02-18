import numpy as np
from datetime import datetime
#from controller.preprocessor import make_thumbnail, make_histogram, make_tif
from controller.preprocessor import SlideProcessor, make_tif, make_mask
from utilities.SqlController import SqlController
from sql_setup import session, dj, database
import sys
import time

# Get the specified schema reference
schema = dj.schema(database)

# Below are the table definitions
@schema
class Animal(dj.Manual):
    definition = """
    prep_id                   : varchar(20) # Name for lab mouse/rat, max 20 chars, primary key
    ---    
    performance_center = NULL : enum("CSHL", "Salk", "UCSD", "HHMI", "Duke")
    date_of_birth = NULL      : date # the mouse's date of birth
    species = NULL            : enum("mouse", "rat")
    strain = NULL             : varchar(50)
    sex = NULL                : enum("M", "F") # (M/F) either 'M' for male, 'F' for female
    genotype = NULL           : varchar(100) # transgenic description, usually "C57"; We will need a genotype table 
    breeder_line = NULL       : varchar(100) # We will need a local breeding table 
    vender = NULL             : enum ("Jackson", "Charles River", "Harlan", "NIH", "Taconic") 
    stock_number = NULL       : varchar(100) # if not from a performance center
    tissue_source = NULL      : enum("animal", "brain", "slides")
    ship_date = NULL          : date
    shipper = NULL            : enum("FedEx", "UPS")
    tracking_number = NULL    : varchar(100)
    aliases_1 = NULL          : varchar(100) # names given by others 
    aliases_2 = NULL          : varchar(100) 
    aliases_3 = NULL          : varchar(100)
    aliases_4 = NULL          : varchar(100)
    aliases_5 = NULL          : varchar(100)
    """

@schema
class ScanRun(dj.Manual):
    definition = """
    id                      : int auto_increment                            
    -> Animal # currently assumes tissue from a single animals on each slide
    ---
    performance_center = NULL    : enum("CSHL", "Salk", "UCSD", "HHMI") # default population is from Histology
    machine = NULL               : enum("Zeiss", "Axioscan", "Nanozoomer","Olympus VA")
    objective = NULL             : enum("60X", "40X", "20X", "10X")
    resolution = 0               : float # (µm) lateral resolution if available
    number_of_slides = 0         : int
    scan_date = NULL             : date
    file_type = NULL             : enum("CZI", "JPEG2000", "NDPI", "NGR")
    scenes_per_slide = NULL      : enum("1", "2", "3", "4", "5", "6")
    section_schema = NULL        : enum("L to R", "R to L") # agreement is one row
    channels_per_scene = NULL    : enum("1", "2", "3", "4")
    slide_folder_path = NULL     : varchar(200) # the path to the slides folder on birdstore (files to be converted)
    converted_folder_path = NULL : varchar(200) # the path to the slides folder on birdstore after convertion
    converted_status = NULL      : enum("not started", "converted", "converting", "error")
    ch_1_filter_set = NULL       : enum("68", "47", "38", "46", "63", "64", "50") # This is counterstain Channel
    ch_2_filter_set = NULL       : enum("68", "47", "38", "46", "63", "64", "50")
    ch_3_filter_set = NULL       : enum("68", "47", "38", "46", "63", "64", "50")
    ch_4_filter_set = NULL       : enum("68", "47", "38", "46", "63", "64", "50")
    """

@schema
class Slide(dj.Manual): # prior to segregation of animals and scenes on each slide
    definition = """
    id : int   auto_increment                                             # one per slide
    -> ScanRun
    ---
    slide_status      : enum("Bad", "Good")
    rescan_number     : enum("", "1", "2", "3")
    scene_qc_1 = ""   : enum("", "Missing one section", "two", "three", "four", "five", "six","O-o-F", "Bad tissue") # Missing are ignored and include folds, dirt over sample 
    scene_qc_2 = ""   : enum("", "Missing one section", "two", "three", "four", "five", "six","O-o-F", "Bad tissue")
    scene_qc_3 = ""   : enum("", "Missing one section", "two", "three", "four", "five", "six","O-o-F", "Bad tissue") 
    scene_qc_4 = ""   : enum("", "Missing one section", "two", "three", "four", "five", "six","O-o-F", "Bad tissue") 
    scene_qc_5 = ""   : enum("", "Missing one section", "two", "three", "four", "five", "six","O-o-F", "Bad tissue") 
    scene_qc_6 = ""   : enum("", "Missing one section", "two", "three", "four", "five", "six","O-o-F", "Bad tissue") #"Bad tissue" is interpretted as one missing section
    file_name = NULL  : varchar(200)               # folder on Birdstore
    """

@schema
class FileOperation(dj.Computed):
    definition = """
    id : int
    -> SlideCziTif
    ---
    file_name :  varchar(200) 
    thumbnail: tinyint
    czi_to_tif: tinyint
    histogram: tinyint
    cleaned: tinyint
    processing_duration: float
    created: datetime
    """

    def make(self, key):
        slide_processor = SlideProcessor(prep_id, session)
        start = time.time()
        file_id = (RawSection & key).fetch1('id')
        file_name = (RawSection & key).fetch1('destination_file')
        file_id = np.asscalar(file_id)
        tif_id = (RawSection & key).fetch1('tif_id')
        czi_to_tif = make_tif(session, prep_id, np.asscalar(tif_id), file_id, testing)
        thumbnail = 0
        cleaned = 0
        histogram = 0
        end = time.time()

        self.insert1(dict(key, file_name=file_name,
                          created=datetime.now(),
                          thumbnail=thumbnail,
                          czi_to_tif = czi_to_tif,
                          cleaned = cleaned,
                          processing_duration=end - start,
                          histogram = histogram), skip_duplicates=False)

# End of table definitions


def manipulate_images(id, limit, testing_param=False):
    global prep_id
    global testing
    prep_id = id
    testing = testing_param
    restriction = 'prep_id = "{}"'.format(prep_id)
    FileOperation.populate([RawSection & 'active=1 ' & restriction ], display_progress=True, reserve_jobs=True, limit=limit)


