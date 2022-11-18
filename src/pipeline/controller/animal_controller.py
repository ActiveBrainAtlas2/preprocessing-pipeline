"""This is the animal SQL controller.
It performs some necessary and simple functions for the animal.
"""

from controller.main_controller import Controller
from database_model.animal import Animal


class AnimalController(Controller):
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)
        
    def get_animal_list(self):
        """Gets a list of animal names

        :returns: a list of animal names
        """

        results = self.session.query(Animal).all()
        animals = []
        for resulti in results:
            animals.append(resulti.prep_id)
        return animals

    def animal_exists(self, animal):
        """A method to test whether an animal exists
        :returns: boolean
        """
        search_dictionary = dict(prep_id=animal)
        return self.row_exists(search_dictionary, Animal)
    
    def get_animal(self, animal):
        """Method to get one specific animal object
        
        :params animal: string of the animal name
        :returns: an animal object
        """

        search_dictionary = dict(prep_id =animal)
        return self.get_row(search_dictionary, Animal)
