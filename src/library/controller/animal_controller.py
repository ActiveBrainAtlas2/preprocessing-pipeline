"""This is the animal SQL controller.
It performs some necessary and simple functions for the animal.
"""
from sqlalchemy.orm.exc import NoResultFound

from library.database_model.animal import Animal


class AnimalController():

    def animal_exists(self, animal) -> bool:
        """A method to test whether an animal exists
        :returns: boolean
        """
        found = False
        search_dictionary = dict(prep_id=animal)
        try:
            found = self.row_exists(search_dictionary, Animal)
        except NoResultFound:
            print(f'No such animal: {animal}')
            found = False
        return found
    
    def get_animal(self, animal):
        """Method to get one specific animal object
        
        :params animal: string of the animal name
        :returns: an animal object
        """

        search_dictionary = dict(prep_id =animal)
        return self.get_row(search_dictionary, Animal)
