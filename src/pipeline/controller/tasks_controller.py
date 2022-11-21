"""This module peforms the CRUD actions for tasks.
"""

from sqlalchemy.orm.exc import NoResultFound

from controller.main_controller import Controller
from database_model.task import Task, ProgressLookup


class TasksController(Controller):    

    def __init__(self, *args, **kwargs):
        """initiates the controller class
        """

        Controller.__init__(self, *args, **kwargs)

    def set_task(self, animal, lookup_id):
        """Look up the lookup up from the step. Check if the animal already exists,
        if not, insert, otherwise, update
        
        :param animal: string of the animal you are working on
        :param lookup_id: current lookup ID
        """
        
        try:
            lookup = (
                self.session.query(ProgressLookup)
                .filter(ProgressLookup.id == lookup_id)
                .limit(1)
                .one()
            )
        except NoResultFound:
            print("No lookup for {} so we will enter one.".format(lookup_id))
        try:
            task = (
                self.session.query(Task)
                .filter(Task.lookup_id == lookup.id)
                .filter(Task.prep_id == animal)
                .one()
            )
        except NoResultFound:
            print("No step for {}, so creating new task.".format(lookup_id))
            task = Task(animal, lookup.id, True)

        try:
            self.session.merge(task)
            self.session.commit()
        except:
            print("Bad lookup code for {}".format(lookup.id))
            self.session.rollback()

    def get_progress_id(self, downsample, channel, action):
        """Gets the primary key for the particular progress ID

        :param downsample: boolean for the downsample/full resolution
        :param channel: integer for channel
        :param action: what step we are doing
        :return: integer primary
        """

        try:
            lookup = (
                self.session.query(ProgressLookup)
                .filter(ProgressLookup.downsample == downsample)
                .filter(ProgressLookup.channel == channel)
                .filter(ProgressLookup.action == action)
                .one()
            )
        except NoResultFound as nrf:
            print(f"Bad lookup code for {downsample} {channel} {action} error: {nrf}")
            return 0

        return lookup.id

    def set_task_for_step(self, animal, downsample, channel, step):
        """Helper method to set a task
        """

        progress_id = self.get_progress_id(downsample, channel, step)
        self.set_task(animal, progress_id)
