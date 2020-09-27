"""
This will query the cvat postgres container for what i believe are the relevant points per:
section (called frame in cvat table engine_labeledshape)
structure (called name in cvat table engine_label)
points (called points in cvat table engine_labledshape)
"""

import argparse
import os, sys
HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)

from cvat_sql_setup import session

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
        print(f"{row.frame}, {row.structure}, {row.points}")

    if len(rows) == 0:
        print(f'No data for task id {task_id}')


if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Task')
    parser.add_argument('--task', help='Enter the task number', required=True)
    args = parser.parse_args()
    task_id = int(args.task)
    display_points(task_id)
