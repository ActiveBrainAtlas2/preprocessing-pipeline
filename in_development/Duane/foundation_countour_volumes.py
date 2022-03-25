'''

CREATED: 24-MAR-2022
LAST EDIT: 24-MAR-2022
AUTHORS: DUANE RINEHART

MODIFY FOUNDATION BRAIN ANNOTATIONS TO GROUP POLYGONS INTO VOLUMES [ACROSS SECTIONS]

'''

import os
import sys
import binascii # unique segment id (contour) ref: https://github.com/google/neuroglancer/blob/master/python/neuroglancer/random_token.py

# WORKAROUND FOR PYTHONPATH (BEFORE OTHER IMPORTS)
src='/net/birdstore/common_programming/pipeline_utility/src'
sys.path.append(src)

from lib.sql_setup import session

dest_db_schema = 'dev2_test'


def update_db(rowid, volume_id):
    '''UPDATE DB WITH CORRECT volume_id (TO IDENTIFY BRAIN REGION/STRUCTURE VOLUMES)'''
    sql_statement = f'UPDATE {dest_db_schema}.annotations_points SET volume_id=\'{volume_id}\' WHERE id=\'{rowid}\''
    #print(sql_statement)
    session.execute(sql_statement)
    session.commit()


def main():
    animals = ['MD585', 'MD589', 'MD594']  # FOUNDATIONAL BRAIN prep_id
    for prep_id in animals:
        print(f"WORKING ON prep_id: {prep_id}")
        sql_statement = f'SELECT *, (SELECT COUNT(DISTINCT(label)) FROM {dest_db_schema}.annotations_points WHERE prep_id=\'{prep_id}\' ORDER BY label ASC, polygon_id ASC) AS CNT_LABELS FROM {dest_db_schema}.annotations_points WHERE prep_id=\'{prep_id}\' ORDER BY label ASC, polygon_id ASC'
        results = session.execute(sql_statement)

        cur_label = ''
        prev_label = ''
        volume_id = binascii.hexlify(os.urandom(20)).decode()  # 20-byte (40 character) random hex string
        for row in results:
            rowid = row['id']
            total_labels = row['CNT_LABELS']
            cur_label = row['label']

            if cur_label != prev_label: #CHANGE label, GENERATE NEW volume_id
                volume_id = binascii.hexlify(os.urandom(20)).decode()  # 20-byte (40 character) random hex string

            update_db(rowid, volume_id)
            prev_label = cur_label


if __name__ == "__main__":
    main()