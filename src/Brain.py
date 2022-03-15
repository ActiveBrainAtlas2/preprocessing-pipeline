from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
from Plotter.Plotter import Plotter
import numpy as np


class Brain:

    def __init__(self, animal):
        self.animal = animal
        self.sqlController = SqlController(self.animal)
        self.path = FileLocationManager(animal)
        self.plotter = Plotter()
        self.attribute_functions = dict(COM=self.load_com,structures=self.set_structures)
        to_um = self.get_resolution()
        self.pixel_to_um = np.array([to_um, to_um, 20])
        self.um_to_pixel = 1 / self.pixel_to_um
    
    def get_resolution(self):
        return self.sqlController.scan_run.resolution
    
    def get_image_dimension(self):
        width = self.sqlController.scan_run.width
        height = self.sqlController.scan_run.height
        return np.array([width, height])
    
    def check_attributes(self, attribute_list):
        assert(hasattr(self , 'attribute_functions'))
        for attribute in attribute_list:
            if not hasattr(self, attribute) or getattr(self, attribute) == {}:
                if attribute in self.attribute_functions:
                    self.attribute_functions[attribute]()
                else:
                    raise NotImplementedError
    
    def get_com_array(self):
        self.check_attributes(['COM'])
        return np.array(list(self.COM.values()))
        
    def load_com(self):
        self.COM = self.sqlController.get_com_dict(self.animal)
    
    def get_shared_coms(self, com_dictionary1, com_dictionary2):
        shared_structures = set(com_dictionary1.keys()).intersection(set(com_dictionary2.keys()))
        values1 = [com_dictionary1[str] for str in shared_structures]
        values2 = [com_dictionary2[str] for str in shared_structures]
        com_dictionary1 = dict(zip(shared_structures, values1))
        com_dictionary2 = dict(zip(shared_structures, values2))
        return com_dictionary1, com_dictionary2
    
    def set_structures(self):
        self.load_com()
        self.structures = self.COM.keys()
    
    def get_structures_from_attribute(self, attribute):
        return list(getattr(self, attribute).keys())
    
    def convert_unit_of_com_dictionary(self, com_dictionary, conversion_factor):
        for structure , com in com_dictionary.items():
            com_dictionary[structure] = np.array(com) * conversion_factor
