from utilities.model.user import User
from sql_setup import session

def get_users():
    query_results = session.query(User).all()
    users = [entryi[0] for entryi in query_results]
    return users