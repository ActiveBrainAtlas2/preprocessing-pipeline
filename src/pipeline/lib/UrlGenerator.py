from abakit.lib.Controllers.SqlController import SqlController
import json 
import numpy as np

class UrlGenerator:
    def __init__(self):
        self.layers = []
        self.controller = SqlController('DK52')
    
    def add_stack_image(self,animal,channel,name=None):
        if name == None:
            name = animal
        source = f'precomputed://https://activebrainatlas.ucsd.edu/data/{animal}/neuroglancer_data/C{channel}'
        self.add_precomputed_image_layer(source,animal)
    
    def add_segmentation_layer(self,folder_name,layer_name):
        segment_layer = dict( type = "segmentation",
                            source = "precomputed://https://activebrainatlas.ucsd.edu/data/structures/" + folder_name,
                            tab = "segments",
                            name = layer_name)
        self.layers.append(segment_layer)

    def add_precomputed_image_layer(self,source,name):
        image_layer = dict( type = "image",
                            source = source,
                            tab = "source",
                            name = name)
        self.layers.append(image_layer)
    
    def add_annotation_layer(self,name,color_hex= None,annotations = None,shader_controls = None):
        if annotations:
            annotation_layer = dict(type =  "annotation",
                                    source=  dict(  url = "local://annotations",
                                                    transform = {}),
                                    name = name)
        if annotations:
            annotation_layer['annotations'] = annotations
        if shader_controls:
            annotation_layer['shaderControls'] = shaderControls
        if color_hex != None:
            annotation_layer = self.insert_annotation_color_hex(annotation_layer,color_hex)
        self.layers.append(annotation_layer)

    def insert_annotation_color_hex(self,annotation_layer,color_hex):
        annotation_layer = annotation_layer.split(',')
        annotation_layer.insert(-2,'\n            "annotationColor": "'+color_hex+'"')
        annotation_layer = ','.join(annotation_layer)
        return annotation_layer

    def get_url(self):
        return json.dumps({'layers': self.layers})
    
    def add_to_database(self,title,person_id):
        content = self.get_url()
        self.controller.add_url(content,title,person_id)
    
    def parse_url(self,url):
        url = json.loads(url.replace('\n',''))
        self.layers = url['layers']
    
    def load_database_url(self,url_id):
        url = self.controller.get_urlModel(url_id)
        self.parse_url(url.url)
    
    def get_layer_with_name(self,name):
        for layer in self.layers:
            if layer['name'] == name:
                return layer

    def get_image_layers(self):
        image_layers = []
        for layer in self.layers:
            if layer['type'] == "image":
                image_layers.append(layer)
        return image_layers
    
    def get_points_from_annotation_layer(self,name):
        layer = self.get_layer_with_name(name)
        annotations = layer['annotations']
        points = []
        for annotation in annotations:
            points.append(annotation['point'])
        return np.array(points)

    