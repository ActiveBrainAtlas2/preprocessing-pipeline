from abakit.lib.Controllers.Controller import Controller
from abakit.model.task import Task,ProgressLookup
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from abakit.model.file_log import FileLog
from datetime import datetime
class TasksController(Controller):
    def __init__(self,*args,**kwargs):
        """initiates the controller class
        """        
        Controller.__init__(self,*args,**kwargs)
        
    def get_current_task(self, animal):
        step = None
        try:
            lookup_id = self.session.query(func.max(Task.lookup_id)).filter(Task.prep_id == animal) \
                .filter(Task.completed.is_(True)).scalar()
        except NoResultFound as nrf:
            print('No results for {} error: {}'.format(animal, nrf))
            return step

        try:
            lookup = self.session.query(ProgressLookup).filter(
                ProgressLookup.id == lookup_id).one()
        except NoResultFound as nrf:
            print('Bad lookup code for {} error: {}'.format(lookup_id, nrf))
            return step

        return lookup.description

    def set_task(self, animal, lookup_id):
        """
        Look up the lookup up from the step. Check if the animal already exists,
        if not, insert, otherwise, update
        Args:
            animal: string of the animal you are working on
            lookup_id: current lookup ID
        Returns:
            nothing, just merges
        """
        try:
            lookup = self.session.query(ProgressLookup) \
                .filter(ProgressLookup.id == lookup_id) \
                .limit(1).one()
        except NoResultFound:
            print('No lookup for {} so we will enter one.'.format(lookup_id))
        try:
            task = self.session.query(Task).filter(Task.lookup_id == lookup.id) \
                .filter(Task.prep_id == animal).one()
        except NoResultFound:
            print('No step for {}, so creating new task.'.format(lookup_id))
            task = Task(animal, lookup.id, True)

        try:
            self.session.merge(task)
            self.session.commit()
        except:
            print('Bad lookup code for {}'.format(lookup.id))
            self.session.rollback()
        
    
    def get_progress_id(self, downsample, channel, action):

        try:
            lookup = self.session.query(ProgressLookup) \
                .filter(ProgressLookup.downsample == downsample) \
                .filter(ProgressLookup.channel == channel) \
                .filter(ProgressLookup.action == action).one()
        except NoResultFound as nrf:
            print(
                f'Bad lookup code for {downsample} {channel} {action} error: {nrf}')
            return 0

        return lookup.id
    
    def set_task_for_step(self,animal,downsample,channel,step):
        progress_id = self.get_progress_id(downsample, channel, step)
        self.set_task(animal, progress_id)
    
    def get_available_actions(self):
        results = self.session.query(ProgressLookup).filter(ProgressLookup.active==1).all()
        for resulti in results:
            print(f'action: {resulti.action}, channel: {resulti.channel}, downsample: {resulti.downsample}')

def file_processed(animal, progress_id, filename,pooledsession):
    """
    Args:
        animal: prep_id
        progress_id: ID from progress_lookup table
        filename: filename you are working on
    Returns:
        boolean if file exists or not
    """
    try:
        file_log = pooledsession.query(FileLog) \
            .filter(FileLog.prep_id == animal) \
            .filter(FileLog.progress_id == progress_id) \
            .filter(FileLog.filename == filename).one()
    except NoResultFound as nrf:
        return False
    finally:
        pooledsession.close()

    return True

def set_file_completed(animal, progress_id, filename,pooledsession):
    """
    Args:
        animal: prep_id
        progress_id: ID from progress_lookup table
        filename: filename you are working on
    Returns:
        nothing, just merges
    """

    file_log = FileLog(prep_id=animal, progress_id=progress_id, filename=filename,
                       created=datetime.utcnow(), active=True)

    try:
        pooledsession.add(file_log)
        pooledsession.commit()
    except Exception as e:
        print(f'No merge for {animal} {filename} {e}')
        pooledsession.rollback()
    finally:
        pooledsession.close()