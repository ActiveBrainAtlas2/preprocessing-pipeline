"""
This will query the cvat postgres container for what i believe are the relevant points per:
section (called frame in cvat table engine_labeledshape)
structure (called name in cvat table engine_label)
points (called points in cvat table engine_labledshape)
you need access to the psql container and this library
pip install psycopg2
You also need to modify the docker container that holds postgres.
Modify the docker-compose.yml file:
services:
　cvat_db:
　　ports:
　　　- "5432:5432"
"""

import argparse
import os, sys
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)

from sql_setup import session

def display_points(task_id):
    """
    Runs a query against 3 cvat tables and prints the results
    Args:
        task_id: This should be the ID of the task on the CVAT tasks page

    Returns: nothing, just prints data now
    """

    query = f"""select el.frame, elab.name as structure, el.points
                from engine_labeledshape el
                inner join engine_job ej on el.job_id = ej.id
                inner join engine_label elab on el.label_id = elab.id
                where elab.task_id = {task_id}
                order by elab.name, el.frame
            """
    rows = session.execute(query).fetchall()
    for row in rows:
        print(f"{row.frame}, {row.structure}, {row.points[0:50]}")

    if len(rows) == 0:
        print(f'No data for task id {task_id}')


if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Task')
    parser.add_argument('--task', help='Enter the task number', required=True)
    args = parser.parse_args()
    task_id = int(args.task)
    display_points(task_id)
