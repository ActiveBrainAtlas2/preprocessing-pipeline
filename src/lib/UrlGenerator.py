class UrlGenerator:
    def __init__(self):
        self.layers = []

    def add_precomputed_image_layer(self,source):
        name = source[source.rfind('/')+1:]
        image_layer = '''
            {
            "type": "image",
            "source": "'''+source+'''",
            "tab": "source",
            "name": "''' +name+'''"
            }
        '''
        self.layers.append(image_layer)
    
    def add_annotation_layer(self,name,color_hex= None):
        annotation_layer = '''
            {
            "type": "annotation",
            "source": {
                "url": "local://annotations",
                "transform": {}
            },
            "annotations": [],
            "name": "'''+name+'''"
            }
        '''
        if color_hex != None:
            annotation_layer = self.insert_annotation_color_hex(annotation_layer,color_hex)
        self.layers.append(annotation_layer)

    def insert_annotation_color_hex(self,annotation_layer,color_hex):
        annotation_layer = annotation_layer.split(',')
        annotation_layer.insert(-2,'\n            "annotationColor": "'+color_hex+'"')
        annotation_layer = ','.join(annotation_layer)
        return annotation_layer

    def get_url(self):
        return '{"layers": ['+ ',\n'.join(self.layers) +']}'