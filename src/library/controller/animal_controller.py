"""This is the animal SQL controller.
It performs some necessary and simple functions for the animal.
"""

from library.database_model.animal import Animal


class AnimalController():

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
