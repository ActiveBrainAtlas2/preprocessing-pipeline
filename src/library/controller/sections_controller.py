from library.controller.main_controller import Controller
from library.database_model.slide import Section

class SectionsController(Controller):
    def __init__(self, *args, **kwargs):
        """initiates the controller class
        """

        Controller.__init__(self, *args, **kwargs)
    
    def get_sections(self, animal, channel, rescan_number):
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
                .filter(Section.rescan_number == rescan_number)\
                .order_by(Section.slide_physical_id.desc())\
                .order_by(Section.scene_number.desc()).all()
        elif slide_orderby == 'ASC' and scene_order_by == 'ASC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .filter(Section.rescan_number == rescan_number)\
                .order_by(Section.slide_physical_id.asc())\
                .order_by(Section.scene_number.asc()).all()
        elif slide_orderby == 'ASC' and scene_order_by == 'DESC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .filter(Section.rescan_number == rescan_number)\
                .order_by(Section.slide_physical_id.asc())\
                .order_by(Section.scene_number.desc()).all()
        elif slide_orderby == 'DESC' and scene_order_by == 'ASC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .filter(Section.rescan_number == rescan_number)\
                .order_by(Section.slide_physical_id.desc())\
                .order_by(Section.scene_number.asc()).all()
        return sections


    def get_section_count(self, animal, rescan_number):
        count = self.session.query(Section)\
            .filter(Section.prep_id == animal)\
            .filter(Section.channel == 1)\
            .filter(Section.rescan_number == rescan_number)\
            .count() 
        return count

    

