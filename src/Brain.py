from lib.sqlcontroller import SqlController
from lib.file_location import FileLocationManager
from atlas.Plotter import Plotter
import numpy as np
class Brain:
    def __init__(self,animal):
        self.animal = animal
        self.sqlController = SqlController(self.animal)
        self.path = FileLocationManager(animal)
        self.plotter = Plotter()
    
    def get_resolution(self):
        return self.sqlController.scan_run.resolution
    
    def get_image_dimension(self):
        width = self.sqlController.scan_run.width
        height = self.sqlController.scan_run.height
        return np.array([width,height])
    
    def check_attributes(self,attribute_list):
        assert(hasattr(self , 'attribute_functions'))
        for attribute in attribute_list:
            if not hasattr(self,attribute) or getattr(self,attribute) == {}:
                if attribute in self.attribute_functions:
                    self.attribute_functions[attribute]()
                else:
                    raise NotImplementedError