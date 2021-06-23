from utilities.model.animal import Animal
from sql_setup import session

def get_active_prep_list():
    query_result = session.query(Animal.prep_id).filter(Animal.active.is_(True)).all()
    preps = [entryi[0] for entryi in query_result]
    preps.remove('Atlas')
    return preps

