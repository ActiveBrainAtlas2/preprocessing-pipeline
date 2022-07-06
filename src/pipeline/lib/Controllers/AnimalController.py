from abakit.lib.Controllers.Controller import Controller
from abakit.model.animal import Animal
class AnimalController(Controller):
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)
        
    def get_animal_list(self):
        results = self.session.query(Animal).all()
        animals = []
        for resulti in results:
            animals.append(resulti.prep_id)
        return animals

    def animal_exists(self,animal):
        search_dictionary = dict(prep_id =animal)
        return self.row_exists(search_dictionary,Animal)
    
    def get_animal(self,animal):
        search_dictionary = dict(prep_id =animal)
        return self.get_row(search_dictionary,Animal)
