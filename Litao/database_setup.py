import datajoint as dj
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

user = 'root'
password = 'ubu=check'
host = 'localhost'
database = 'atlas_test'

connection_string = f'mysql+pymysql://{user}:{password}@{host}/{database}'
engine = create_engine(connection_string, echo=False)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()

dj.config['database.user'] = user
dj.config['database.password'] = password
dj.config['database.host'] = host
dj.conn()
schema = dj.schema(database)
schema.spawn_missing_classes()
