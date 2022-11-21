from controller.main_controller import Controller
from database_model.slide import Section

class SectionsController(Controller):
    def __init__(self, *args, **kwargs):
        """initiates the controller class
        """

        Controller.__init__(self, *args, **kwargs)
        
    def get_section(self, ID):
        """The sections table is a view and it is already filtered by active and file_status = 'good'
        This qeury returns a single section by id.
        
        :param id: integer primary key

        :returns: one section
        """

        return self.session.query(Section).get(ID)
    
    def get_sections(self, animal, channel):
        """The sections table is a view and it is already filtered by active and file_status = 'good'
        The ordering is important. This needs to come from the histology table.

        :param animal: the animal to query
        :param channel: 1 or 2 or 3.

        :returns: list of sections in order

        """
        slide_orderby = self.histology.side_sectioned_first
        scene_order_by = self.histology.scene_order
        if slide_orderby == 'DESC' and scene_order_by == 'DESC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .order_by(Section.slide_physical_id.desc())\
                .order_by(Section.scene_number.desc()).all()
        elif slide_orderby == 'ASC' and scene_order_by == 'ASC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .order_by(Section.slide_physical_id.asc())\
                .order_by(Section.scene_number.asc()).all()
        elif slide_orderby == 'ASC' and scene_order_by == 'DESC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .order_by(Section.slide_physical_id.asc())\
                .order_by(Section.scene_number.desc()).all()
        elif slide_orderby == 'DESC' and scene_order_by == 'ASC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .order_by(Section.slide_physical_id.desc())\
                .order_by(Section.scene_number.asc()).all()
        return sections
    
    def get_sections_numbers(self, animal):
        """Get all the section numbers from an animal

        :param animal: animal key
        :return section_numbers: a list of the sections
        """

        sections = self.session.query(Section).filter(
            Section.prep_id == animal).filter(Section.channel == 1).all()
        section_numbers = []
        for i, r in enumerate(sections):
            section_numbers.append(i)
        return section_numbers

    def get_sections_dict(self, animal):
        """Gets a dictionary of sections by animal

        
        :param animal: animal key
        :return section_numbers: a dictionary of the sections
        """

        sections = self.session.query(Section).filter(
            Section.prep_id == animal).filter(Section.channel == 1).all()

        sections_dict = {}
        for i, r in enumerate(sections):
            sections_dict[i] = str(i).zfill(3) + 'tif'

        return sections_dict

    def get_section_count(self, animal):
        """Get the number of sections by animal

        :param animal: animal key
        :return section_numbers: a integer of the count
        """
        try:
            count = self.session.query(Section).filter(
                Section.prep_id == animal).filter(Section.channel == 1).count()
        except:
            count = 666
        return count
    
    def get_distinct_section_filenames(self, animal, channel):
        """Very similar to the get_sections query but this will return a list of
        distinct file names. Since some of the scenes get duplicated in the QA process,
        we need to get the tifs without duplicates. The duplicates will then get replicated
        with the get_sections method. The order doesn't matter here.

        :param animal: the animal to query
        :param channel: 1 or 2 or 3.

        :returns: list of sections with distinct file names

        """
        sections = self.session.query(Section.czi_file, Section.file_name, Section.scene_number,  Section.channel_index).distinct()\
            .filter(Section.prep_id == animal).filter(
            Section.channel == channel).all()

        return sections
