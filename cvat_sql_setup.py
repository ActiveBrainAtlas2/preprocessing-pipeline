import yaml
import os, sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
dirname = os.path.dirname(__file__)
file_path = os.path.join(dirname, 'cvat.yaml')

try:
        with open(file_path) as file:
            parameters = yaml.load(file, Loader=yaml.FullLoader)
except:
    print('Could not open cvat.yml')
    sys.exit()

user = parameters['user']
password = parameters['password']
host = parameters['host']
database = parameters['schema']

connection_string = f'postgresql+psycopg2://{user}:{password}@{host}:5432/{database}'

engine = create_engine(connection_string, echo=False)
DBSession = sessionmaker(bind=engine)
session = DBSession()

