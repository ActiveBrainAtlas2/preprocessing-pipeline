from abakit.model.structure import Structure
from sqlalchemy import func
from abakit.lib.Controllers.Controller import Controller
from sqlalchemy.orm.exc import NoResultFound

class StructuresController(Controller):

    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)

    def get_structure_color(self, abbrv):
        """
        Returns a color code as int
        This search has to be case sensitive!
        :param abbrv: the abbreviation of the structure
        :return: tuple of rgb
        """
        row = self.session.query(Structure).filter(
            Structure.abbreviation == func.binary(abbrv)).one()
        return int(row.color)

    def get_structure_color_rgb(self, abbrv):
        """
        Returns a color code in RGB format like (1,2,3)
        This search has to be case sensitive!
        :param abbrv: the abbreviation of the structure
        :return: tuple of rgb
        """
        row = self.session.query(Structure).filter(
            Structure.abbreviation == func.binary(abbrv)).one()
        hexa = row.hexadecimal
        h = hexa.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def get_structures(self):
        """return a list of active structures

        Returns:
            list: list of structure ORM
        """        
        return self.session.query(Structure).filter(Structure.active.is_(True)).all()

    def get_structure_description_and_color(self):
        """returns the dictionary of structure abbreviation,description and color

        Returns:
            dict: dictionary of structure description and color indexes by structure abbreviation
        """        
        rows = self.session.query(Structure)\
            .filter(Structure.abbreviation != 'R')\
            .filter(Structure.is_structure ==1).filter(
            Structure.active.is_(True)).all()
        structures_dict = {}
        for structure in rows:
            structures_dict[structure.abbreviation] = [
                structure.description, structure.color]

        return structures_dict

    def get_sided_structures(self):
        """
        Return a list of sided structures
        :return: list of structures that exists as pairs on both side of the brain. 
        i.e. structures that is not in the midline
        """
        rows = self.session.query(Structure).filter(
            Structure.active.is_(True)).all()
        structures = []
        for structure in rows:
            if "_" in structure.abbreviation:
                structures.append(structure.abbreviation)

        return sorted(structures)

    def get_structure(self, abbrv):
        """
        Returns a structure ORM object
        This search has to be case sensitive!
        :param abbrv: the abbreviation of the structure
        :return: structure object
        """
        return self.session.query(Structure).filter(Structure.abbreviation == func.binary(abbrv)).one()
    
        
    def structure_abbreviation_to_id(self,abbreviation):
        try:
            structure = self.get_structure(str(abbreviation).strip())
        except NoResultFound as nrf:
            print(f'No structure found for {abbreviation} {nrf}')
            return
        return structure.id

    def get_segment_to_id_where_segment_are_brain_regions(self):
        db_structure_infos = self.get_structure_description_and_color()
        segment_to_id = {}
        for structure, (_, number) in db_structure_infos.items():
            segment_to_id[structure] = number
        return segment_to_id