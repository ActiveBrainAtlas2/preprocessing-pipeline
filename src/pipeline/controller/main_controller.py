"""This is the main SQL controller class. All the other
controller classes inherit from this class and use it. It 
creates a bunch of basic SQL statements that come in handy for the other controllers.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session


def create_session(host, password, schema, user):
    """Create a session scoped session. A session will last
    24 hours.

    :param host: The database server to connect to
    :param password: string kept in the settings.py file in the users home
    :param schema: which database schema to use.
    :param user: connect to the database with which user
    """

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

        :param row: a row of a database table.
        """

        try:
            self.session.merge(row)
            self.session.commit()
        except Exception as e:
            print(f'No merge for  {e}')
            self.session.rollback()
    
    def add_row(self, data):
        """adding a row to a table

        :param data: (data to be added ): instance of sqalchemy ORMs
        """

        try:
            self.session.add(data)
            self.session.commit()
        except Exception as e:
            print(f'No merge {e}')
            self.session.rollback()

    
    def get_row(self, search_dictionary, model):
        """look for a specific row in the database and return the result

        :param search_dictionary: (dict): field and value of the search
        :param model: (sqalchemy ORM): the sqalchemy ORM in question 

        :return:  sql alchemy query
        """ 

        query_start = self.session.query(model)
        exec(f'from {model.__module__} import {model.__name__}')
        for key, value in search_dictionary.items():
            query_start = eval(f'query_start.filter({model.__name__}.{key}=="{value}")')
        return query_start.one()
    
    def row_exists(self,search_dictionary,model):
        """check if a specific row exist in a table

        
        :param search_dictionary: (dict): field and value for the search
        :param model: (sqalchemy ORM): sqalchemy ORM

        :return boolean: whether the row exists
        """

        return self.get_row(search_dictionary,model) is not None
    
    def query_table(self,search_dictionary,model):
        """query a sql table and return all the results fitting the search criterias

        :param search_dictionary: (dict): search field and value
        :param model: (sqalchemy ORM class): sqalchemy ORM

        returns list: the query result in a list of ORM objects 
        """

        query_start = self.session.query(model)
        exec(f'from {model.__module__} import {model.__name__}')
        for key, value in search_dictionary.items():
            query_start = eval(f'query_start.filter({model.__name__}.{key}=="{value}")')
        return query_start.all()
    
    def delete_row(self, search_dictionary, model):
        """Deletes one row of any table

        :param search_dictionary: (dict): search field and value
        :param model: (sqalchemy ORM class): sqalchemy ORM
        """

        row = self.get_row(search_dictionary,model)
        self.session.delete(row)
        self.session.commit()