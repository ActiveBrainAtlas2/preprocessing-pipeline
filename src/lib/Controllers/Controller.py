from lib.sql_setup import session, pooledsession

class Controller(object):
    def __init__(self):
        """ setup the attributes for a sql session
        """
        self.session = session
    
    def update_row(self, row):
        try:
            self.session.merge(row)
            self.session.commit()
        except Exception as e:
            print(f'No merge for  {e}')
            self.session.rollback()
    
    def add_row(self,data):
        try:
            self.session.add(data)
            self.session.commit()
        except Exception as e:
            print(f'No merge {e}')
            self.session.rollback()
        finally:
            self.session.close()