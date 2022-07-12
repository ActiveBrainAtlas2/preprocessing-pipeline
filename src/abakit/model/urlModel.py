from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, TIMESTAMP
from .atlas_model import Base, AtlasModel
import re
import json

class UrlModel(Base, AtlasModel):
    __tablename__ = 'neuroglancer_urls'
    id =  Column(Integer, primary_key=True, nullable=False)
    url = Column(String, nullable=False)
    person_id = Column(Integer, nullable=False)
    vetted = Column(Boolean, default=False, nullable=False)
    updated = Column(TIMESTAMP)
    comments = Column(String)

    def get_animal(self):
        """Find the animal within the url between data/ and /neuroglancer_data:
        data/MD589/neuroglancer_data/C1
        
        :return: the first match if found, otherwise NA
        """
        animal = "NA"
        match = re.search('data/(.+?)/neuroglancer_data', str(self.url))
        neuroglancer_json = json.loads(self.url)
        image_layers = [layer for layer in neuroglancer_json['layers'] if layer['type'] == 'image']
        if len(image_layers) >0:
            first_image_layer = json.dumps(image_layers[0])
            match = re.search('data/(.+?)/neuroglancer_data', first_image_layer)
            if match is not None and match.group(1) is not None:
                animal = match.group(1)
        return animal





