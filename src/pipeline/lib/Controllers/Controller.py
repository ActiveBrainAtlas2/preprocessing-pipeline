from abakit.settings import user,password,host,schema
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from time import sleep
from sqlalchemy.exc import OperationalError
def create_session(host,schema,max_attempt = 50):
    success = False
    attempt=0
    while not success and attempt<max_attempt:
            try:
                connection_string = f'mysql+pymysql://{user}:{password}@{host}/{schema}?charset=utf8'
                engine = create_engine(connection_string, echo=False)
                Session = sessionmaker(bind=engine)
                success  = True
            except OperationalError:
                attempt+=1
                sleep(5)
    return Session()

def create_pooled_session(host,schema,max_attempt = 50):
    success = False
    attempt=0
    while not success and attempt<max_attempt:
            try:
                connection_string = f'mysql+pymysql://{user}:{password}@{host}/{schema}?charset=utf8'
                pooledengine = create_engine(connection_string, pool_size=10, max_overflow=50, pool_recycle=3600)
                success  = True
            except OperationalError:
                attempt+=1
                sleep(5)
    return scoped_session(sessionmaker(bind=pooledengine)) 

class Controller(object):
    def __init__(self, host=host, schema=schema):
        """ setup a sqalchemy session
        """
        self.host = host
        self.schema = schema
        self.session,self.pooledsession = self.get_session()

    def get_session(self):
        session = create_session(self.host,self.schema)
        pooledsession = create_pooled_session(self.host,self.schema)
        success = True
        return session,pooledsession

    def update_row(self, row):
        """update one row of a database

        Args:
            row (sqalchemy query result): resulting object of a sqalchemy query
        """        
        try:
            self.session.merge(row)
            self.session.commit()
        except Exception as e:
            print(f'No merge for  {e}')
            self.session.rollback()
    
    def add_row(self,data):
        """adding a row to a table

        Args:
            data (data to be added ): instance of sqalchemy ORMs
        """        
        try:
            self.session.add(data)
            self.session.commit()
        except Exception as e:
            print(f'No merge {e}')
            self.session.rollback()

    
    def get_row(self,search_dictionary,model):
        """look for a specific row in the database and return the result

        Args:
            search_dictionary (dict): field and value of the search
            model (sqalchemy ORM): the sqalchemy ORM in question 

        Returns:
            _type_: _description_
        """ 
        query_start = self.session.query(model)
        exec(f'from {model.__module__} import {model.__name__}')
        for key, value in search_dictionary.items():
            query_start = eval(f'query_start.filter({model.__name__}.{key}=="{value}")')
        return query_start.one()
    
    def row_exists(self,search_dictionary,model):
        """check if a specific row exist in a table

        Args:
            search_dictionary (dict): field and value for the search
            model (sqalchemy ORM): sqalchemy ORM

        Returns:
            boolearn: whether the row exists
        """
        return self.get_row(search_dictionary,model) is not None
    
    def query_table(self,search_dictionary,model):
        """query a sql table and return all the results fitting the search criterias

        Args:
            search_dictionary (dict): search field and value
            model (sqalchemy ORM class): sqalchemy ORM

        Returns:
            list: the query result in a list of ORM objects 
        """        
        query_start = self.session.query(model)
        exec(f'from {model.__module__} import {model.__name__}')
        for key, value in search_dictionary.items():
            query_start = eval(f'query_start.filter({model.__name__}.{key}=="{value}")')
        return query_start.all()
    
    def delete_row(self,search_dictionary,model):
        row = self.get_row(search_dictionary,model)
        self.session.delete(row)
        self.session.commit()