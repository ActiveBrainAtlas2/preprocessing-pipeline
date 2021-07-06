from utilities.model.COM_type import ComType
from sql_setup import session

def get_input_types():
    query_results = session.query(ComType).all()
    com_type = [entryi[0] for entryi in query_results]
    return com_type