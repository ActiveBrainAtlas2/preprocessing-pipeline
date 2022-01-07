from model.structure import Structure
from sqlalchemy import func
from lib.Controllers.Controller import Controller

class StructuresController(Controller):

    def __init__(self):
        super().__init__()

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
        return self.session.query(Structure).filter(Structure.active.is_(True)).all()

    def get_structures_dict(self):
        rows = self.session.query(Structure)\
            .filter(Structure.abbreviation != 'R')\
            .filter(Structure.is_structure ==1).filter(
            Structure.active.is_(True)).all()
        structures_dict = {}
        for structure in rows:
            structures_dict[structure.abbreviation] = [
                structure.description, structure.color]

        return structures_dict

    def get_structures_list(self):
        rows = self.session.query(Structure).filter(Structure.id<52)\
                .filter(Structure.abbreviation != 'R').filter(Structure.active.is_(
            True)).order_by(Structure.abbreviation.asc()).all()
        structures = []
        for structure in rows:
            structures.append(structure.abbreviation)

        return structures

    def get_sided_structures(self):
        """
        Not sure when/if this is needed, but will only return sided structures
        :return: list of structures that are not singules
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
        Returns a structure
        This search has to be case sensitive!
        :param abbrv: the abbreviation of the structure
        :return: structure object
        """
        return self.session.query(Structure).filter(Structure.abbreviation == func.binary(abbrv)).one()