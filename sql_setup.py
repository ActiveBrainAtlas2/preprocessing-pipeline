import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datajoint as dj
import os
dirname = os.path.dirname(__file__)
file_path = os.path.join(dirname, 'parameters.yaml')
with open(file_path) as file:
    parameters = yaml.load(file, Loader=yaml.FullLoader)

user = parameters['user']
password = parameters['password']
host = parameters['host']
database = parameters['schema']
connection_string = 'mysql+pymysql://{}:{}@{}/{}'.format(user, password, host, database)
engine = create_engine(connection_string, echo=False)
DBSession = sessionmaker(bind=engine)
session = DBSession()

##### DJ parameters
# Connect to the datajoint database
dj.config['database.user'] = user
dj.config['database.password'] = password
dj.config['database.host'] = host
dj.conn()


##### Lookup IDs

SLIDES_ARE_SCANNED = 1
CZI_FILES_ARE_PLACED_ON_BIRDSTORE = 2
CZI_FILES_ARE_SCANNED_TO_GET_METADATA = 3
QC_IS_ONE_ON_SLIDES_IN_ADMIN_AREA  = 4
SECTION_LIST_IS_CREATED_AND_EXPORTED = 5
CZI_FILES_ARE_CONVERTED_INTO_TIFS_AND_HISTOGRAMS = 6
THUMBNAILS_ARE_CREATED = 7
#NUMBERED_SECTION_CHANNEL_1_FILES_ARE_PLACED_IN_PREPS/CH1/FULL_CLEANED       8
#NUMBERED SECTION CHANNEL 2 FILES ARE PLACED IN PREPS/CH2/FULL_CLEANED       9
#NUMBERED SECTION CHANNEL 3 FILES ARE PLACED IN PREPS/CH3/FULL_CLEANED      10
#NUMBERED THUMBNAIL CHANNEL 1 FILES ARE PLACED IN PREPS/CH1/FULL_THUMBNAIL  11
#NUMBERED THUMBNAIL CHANNEL 2 FILES ARE PLACED IN PREPS/CH1/FULL_THUMBNAIL  12
#NUMBERED THUMBNAIL CHANNEL 3 FILES ARE PLACED IN PREPS/CH3/FULL_THUMBNAIL  13
#CREATE MASKS AND PLACE IN PREPS/THUMBNAIL_MASK                             14
#CLEAN CHANNEL 1 THUMBNAIL WITH MASK                                        15
#CLEAN CHANNEL 2 THUMBNAIL WITH MASK                                        16
#CLEAN CHANNEL 3 THUMBNAIL WITH MASK                                        17
#ALIGN CHANNEL 1 THUMBNAILS WITH ELASTIX                                    18
#ALIGN CHANNEL 2 THUMBNAILS WITH ELASTIX                                    19
#ALIGN CHANNEL 3 THUMBNAILS WITH ELASTIX                                    20
#RUN PRECOMPUTE NEUROGLANCER CHANNEL 1 THUMBNAILS                           21
#RUN PRECOMPUTE NEUROGLANCER CHANNEL 2 THUMBNAILS                           22
#RUN PRECOMPUTE NEUROGLANCER CHANNEL 3 THUMBNAILS                           23
#CURATE RESULTS IN NEUROGLANCER                                             24
