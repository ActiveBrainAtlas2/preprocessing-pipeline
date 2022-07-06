from abakit.lib.Controllers.SqlController import SqlController
import json 
import numpy as np

class UrlGenerator:
    def __init__(self):
        self.layers = []
        self.controller = SqlController('DK52')
    
    def add_stack_image(self,animal,channel,name=None,color = None):
        if not hasattr(self,'dimensions'):
            self.dimensions = self.controller.get_resolution(animal)/(10**6)
        if name == None:
            name = animal
        rgb_code = dict(red = 'vec3(pix,0,0)',green = 'vec3(0,pix,0)')
        source = f'precomputed://https://activebrainatlas.ucsd.edu/data/{animal}/neuroglancer_data/C{channel}'
        if color is not None:
            shader = '''#uicontrol invlerp normalized  (range=[0,5000])
                        #uicontrol float gamma slider(min=0.05, max=2.5, default=1.0, step=0.05)
                        #uicontrol bool colour checkbox(default=true)
                        void main() {
                            float pix =  normalized();
                            pix = pow(pix,gamma);
                            if (colour) {
                            emitRGB(vec3('''+rgb_code[color]+'''));
                            } else {
                            emitGrayscale(pix) ;
                            }
                        }
                        '''
        else:
            shader ='''
                    #uicontrol invlerp normalized
                    #uicontrol float gamma slider(min=0.05, max=2.5, default=1.0, step=0.05)
                    void main() {
                        float pix =  normalized();
                        pix = pow(pix,gamma);
                        emitGrayscale(pix) ;
                    }
                    '''
        self.add_precomputed_image_layer(source,animal,shader)
    
    def add_segmentation_layer(self,folder_name,layer_name):
        segment_layer = dict( type = "segmentation",
                            source = "precomputed://https://activebrainatlas.ucsd.edu/data/structures/" + folder_name,
                            tab = "segments",
                            name = layer_name)
        self.layers.append(segment_layer)

    def add_precomputed_image_layer(self,source,name,shader=None):
        image_layer = dict( type = "image",
                            source = source,
                            tab = "source",
                            name = name)
        if shader is not None:
            image_layer['shader']=shader
        self.layers.append(image_layer)
    
    def add_annotation_layer(self,name,color_hex= None,annotations = None):
        annotation_layer = dict(type =  "annotation",
                                source=  dict(  url = "local://annotations"),
                                tab = 'annotations',
                                annotations = [],
                                name = name)
        if annotations is not None:
            annotation_layer['annotations'] = annotations
        if color_hex is not None:
            annotation_layer = self.insert_annotation_color_hex(annotation_layer,color_hex)
        self.layers.append(annotation_layer)

    def insert_annotation_color_hex(self,annotation_layer,color_hex):
        annotation_layer = annotation_layer.split(',')
        annotation_layer.insert(-2,'\n            "annotationColor": "'+color_hex+'"')
        annotation_layer = ','.join(annotation_layer)
        return annotation_layer

    def get_url(self):
        if hasattr(self,'dimensions'):
            return json.dumps({'dimensions':{'x':[self.dimensions[0],'m'],'y':[self.dimensions[1],'m'],'z':[self.dimensions[2],'m']},'layers': self.layers})
        else:
            return json.dumps({'layers': self.layers})
    
    def add_to_database(self,title,person_id):
        content = self.get_url()
        id = self.controller.add_url(content,title,person_id)
        return id
    
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
