import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cell_model import Cell

class Controller:
    def __init__(self,database):
        self.data_base = database
        self.start_session()
    
    def start_session(self):
        file_path = r'/data/programming/pipeline/parameters.yaml'
        with open(file_path) as file:
            parameters = yaml.load(file, Loader=yaml.FullLoader)
        user = parameters['user']
        password = parameters['password']
        host = parameters['host']
        connection_string = f'mysql+pymysql://{user}:{password}@{host}/{self.data_base}?charset=utf8'
        engine = create_engine(connection_string, echo=False)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def add_row(self,data):
        try:
            self.session.add(data)
            self.session.commit()
        except Exception as e:
            print(f'No merge {e}')
            self.session.rollback()

class FeaturesController(Controller):
    def __init__(self):
        super().__init__(database = 'dk_data')
    
    def get_cell_by_id(self,id):
        return self.session.query(Cell).filter(Cell.id == id).first()
    
    def drop_cell_by_id(self,id):
        self.session.query(Cell).filter(Cell.id == id).delete(synchronize_session=False)
    
    def get_cells_in_range(self,x_range,y_range,z_range):
        result = self.session.query(Cell)\
            .filter(Cell.x.between(x_range[0], x_range[1]))\
            .filter(Cell.x.between(y_range[0], y_range[1]))\
            .filter(Cell.x.between(z_range[0], z_range[1])).all()
        return result