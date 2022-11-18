from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session


def create_session(host, password, schema, user):
    connection_string = f'mysql+pymysql://{user}:{password}@{host}/{schema}?charset=utf8'
    timeout = 60 * 60 * 24 # = 24 hours
    engine = create_engine(connection_string, connect_args={'connect_timeout': timeout})
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    return Session()


class Controller(object):
    def __init__(self, host, password, schema, user):
        """ setup a sqalchemy session
        """
        self.session = create_session(host, password, schema, user)

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