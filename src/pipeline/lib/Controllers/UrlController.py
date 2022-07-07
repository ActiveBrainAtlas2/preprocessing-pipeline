from abakit.model.urlModel import UrlModel
from abakit.lib.Controllers.Controller import Controller
class UrlController(Controller):
    """The sqlalchemy controller to query the neuroglancer url table
    """    

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)

    def url_exists(self,comments):
        """checking if a url entry exists

        Args:
            comments (str): the title of the url

        Returns:
            bool: if a row exists
        """        
        row_exists = bool(self.session.query(UrlModel).filter(UrlModel.comments == comments).first())
        return row_exists
    
    def add_url(self,content,title,person_id):
        """Adding a row to the neuroglancer url table

        Args:
            content (str): string version of the neuroglancer json state
            title (str): title of neuroglancer url
            person_id (int): annotator id
        """        
        url = UrlModel(url = content,comments = title,person_id = person_id)
        self.add_row(url)
        return url.id

    def delete_url(self,title,person_id):
        """Deleting a row from the neuroglancer url table

        Args:
            title (str): title of neuroglancer url
            person_id (int): annotator id
        """        
        self.session.query(UrlModel)\
            .filter(UrlModel.comments == title)\
            .filter(UrlModel.person_id == person_id).delete()
        self.session.commit()
    
    def get_urlModel(self, ID):
        """getting the sqlalchemy orm from the neuroglancer url table of a specific id (primary index for the table)

        Args:
            ID (int): url model id

        Returns:
            UrlModel: Sqlalchemy orm object
        """        
        return self.session.query(UrlModel).filter(UrlModel.id == ID).one()

    def get_url_id_list(self):
        """getting a list of available url ids

        Returns:
            list: list of url ids
        """        
        urls = self.session.query(UrlModel).all()
        ids = [url.id for url in urls]
        return ids