from lib.UrlGenerator import UrlGenerator
import pickle
from abakit.lib.SqlController import SqlController
import numpy as np
controller = SqlController('DK52')

def add_affine_points_to_database(animal):
    com = coms[animal]
    for structure, coordinate in com.items():
        print(structure,coordinate)
        x,y,section = coordinate
        structureid = controller.structure_abbreviation_to_id(structure)
        if not controller.layer_data_row_exists(animal=animal,person_id=Beth,input_type_id=Detected,structure_id=structureid,layer=layer):
            controller.add_layer_data( abbreviation = structure, animal = animal, 
                                layer = layer, x = x, y = y, section = section, 
                            person_id = Beth, input_type_id = Detected)

def generate_url(animal,title):
    generator = UrlGenerator()
    generator.add_stack_image(animal,channel=1)
    generator.add_annotation_layer('Manual')
    generator.add_annotation_layer('Affine Transformed Atlas Com',color_hex='#00eeff')
    generator.add_to_database(title =title ,person_id = 34)

if __name__ == '__main__':
    path = '/home/zhw272/Downloads/AtlasCOMsStack.pkl'
    file = open(path,'rb')
    coms = pickle.load(file)
    animals = list(coms.keys())
    Beth = 2
    Detected = 3
    layer =  'affine_transformed_COM'
    for animal in animals:
        add_affine_points_to_database(animal)
        title = f'{animal} Automatic Alignment'
        if not controller.url_exists(comments = title):
            generate_url(animal,title)