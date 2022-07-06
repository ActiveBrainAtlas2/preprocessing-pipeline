from abakit.model.urlModel import UrlModel

class UrlController:
        
    def url_exists(self,comments):
        row_exists = bool(self.session.query(UrlModel).filter(UrlModel.comments == comments).first())
        return row_exists
    
    def add_url(self,content,title,person_id):
        url = UrlModel(url = content,comments = title,person_id = person_id)
        self.add_row(url)

    def delete_url(self,title,person_id):
        self.session.query(UrlModel)\
            .filter(UrlModel.comments == title)\
            .filter(UrlModel.person_id == person_id).delete()
        self.session.commit()
    
    def get_urlModel(self, ID):
        """
        Args:
            id: integer primary key

        Returns: one neuroglancer json object
        """
        return self.session.query(UrlModel).filter(UrlModel.id == ID).one()

    def get_url_id_list(self):
        urls = self.session.query(UrlModel).all()
        ids = [url.id for url in urls]
        return ids