import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
#import datajoint as dj
import os

dirname = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..','..'))
file_path = os.path.join(dirname, 'parameters.yaml')
with open(file_path) as file:
    parameters = yaml.load(file, Loader=yaml.FullLoader)

user = parameters['user']
password = parameters['password']
host = parameters['host']
database = parameters['schema']
connection_string = f'mysql+pymysql://{user}:{password}@{host}/{database}?charset=utf8'
engine = create_engine(connection_string, echo=False)
Session = sessionmaker(bind=engine)
session = Session()


pooledengine = create_engine(connection_string, pool_size=10, max_overflow=50, pool_recycle=3600)
pooledsession = scoped_session(sessionmaker(bind=pooledengine)) 

##### DJ parameters
# Connect to the datajoint database
#dj.config['database.user'] = user
#dj.config['database.password'] = password
#dj.config['database.host'] = host
#dj.conn()
#schema = dj.schema(database)
#schema.spawn_missing_classes()


##### Lookup IDs

SLIDES_ARE_SCANNED = 10
CZI_FILES_ARE_PLACED_ON_BIRDSTORE = 20
CZI_FILES_ARE_SCANNED_TO_GET_METADATA = 30
QC_IS_DONE_ON_SLIDES_IN_WEB_ADMIN = 40
CZI_FILES_ARE_CONVERTED_INTO_NUMBERED_TIFS_FOR_CHANNEL_1 = 50
CREATE_CHANNEL_1_FULL_RES = 55
CREATE_CHANNEL_2_FULL_RES = 130
CREATE_CHANNEL_3_FULL_RES = 160
CREATE_CHANNEL_1_THUMBNAILS = 60
CREATE_CHANNEL_2_THUMBNAILS = 140
CREATE_CHANNEL_3_THUMBNAILS = 170
CREATE_CHANNEL_1_HISTOGRAMS = 70
CREATE_THUMBNAIL_MASKS = 80
CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK = 90
ALIGN_CHANNEL_1_THUMBNAILS_WITH_ELASTIX = 100
CREATE_FULL_RES_MASKS = 120
CREATE_CHANNEL_2_HISTOGRAMS = 150
CREATE_CHANNEL_3_HISTOGRAMS = 180
CLEAN_CHANNEL_1_FULL_RES_WITH_MASK = 185
CLEAN_CHANNEL_2_FULL_RES_WITH_MASK = 190
CLEAN_CHANNEL_3_FULL_RES_WITH_MASK = 200
ALIGN_CHANNEL_1_FULL_RES = 209
ALIGN_CHANNEL_2_FULL_RES = 210
ALIGN_CHANNEL_3_FULL_RES = 220
RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_1_LOW_RES = 225
RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_LOW_RES = 230
RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_LOW_RES = 240
RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_1_FULL_RES = 245
RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_2_FULL_RES = 250
RUN_PRECOMPUTE_NEUROGLANCER_CHANNEL_3_FULL_RES = 255
