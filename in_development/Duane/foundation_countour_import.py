'''
IMPORT FOUNDATION BRAIN IMAGES' VERTICIES INTO DB

CREATED: 8-MAR-2022
LAST EDIT: 16-MAR-2022
AUTHORS: ZHONGKAI AND DUANE

READ FOUNDATION BRAIN IMAGE ANNOTATIONS AND INSERT INTO DB

'''

import os
import sys
import binascii # unique segment id (contour) ref: https://github.com/google/neuroglancer/blob/master/python/neuroglancer/random_token.py

# WORKAROUND FOR PYTHONPATH (BEFORE OTHER IMPORTS)
src='/net/birdstore/common_programming/pipeline_utility/src'
sys.path.append(src)

from atlas.FoundationContourAligner import FoundationContourAligner
data_src = os.path.join('/net/birdstore/Active_Atlas_Data/data_root/atlas_data/foundation_brain_annotations')


# TESTING - SAVE TO CSV
import pandas as pd


# FOR SAVE TO DB
from pipeline.lib.sql_setup import session
from model.structure import Structure


dest_db_schema = 'dev2_test'


def insert_into_db(prep_id, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering_int):

    sql_statement = f'INSERT INTO {dest_db_schema}.annotations_points (prep_id, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering) VALUES (\'{prep_id}\',\'{FK_structure_id}\', \'{FK_owner_id}\', \'{FK_input_id}\', \'{label}\',  \'{x}\', \'{y}\', \'{z}\', \'{active}\', \'{segment_id}\', \'{ordering_int}\')'
    session.execute(sql_statement)
    session.commit()


def get_structure_table_correspondance():
    rows = session.query(Structure).all()
    results = {}
    for row in rows:
        results[row.abbreviation] = [row.id, row.description]
    return results


#SINGLE QRY TO GET STRUCTURE DATA
structure_data = get_structure_table_correspondance()


# DEFAULTS
animals = ['MD585', 'MD589', 'MD594'] #FOUNDATIONAL BRAIN prep_id
#animals = ['MD589', 'MD594']
FK_owner_id = '4' #ALL OWNED BY USER 'dk'
FK_input_id = '1' #ALL MANUAL
active = '1'

for animal in animals:
    aligner = FoundationContourAligner(animal, atlas='atlasV8')
    aligner.load_contours_for_Foundation_brains()

    # FOR DEBUG 
    # df = pd.DataFrame.from_dict(aligner.contour_per_structure_per_section)
    # df.to_csv(f"/home/drinehart/out_no_densify_{animal}.csv")

    output = ""
    for skey, value in aligner.contour_per_structure_per_section.items():

        output += f"DEBUG - [{animal}] (structure):" + str(skey) + "; QTY:" + str(len(value)) + "\n"
        #print("DEBUG - (section):", skey, "; QTY:", len(value))
        #pull FK_structure_id from structure table (in db) where abbreviation = structure name (key)
        FK_structure_data = structure_data.get(skey) #LOOKUP STRUCTURE ID
        FK_structure_id = FK_structure_data[0]
        label = FK_structure_data[1]
        

        
        for z, value1 in value.items():

            # FILTER PROBLEMATIC SETS *WILL ADD LATER
            if animal == 'MD594' and str(skey) == 'VLL_R' and (str(z) == '300' or str(z) == '308'):
                continue
            if animal == 'MD594' and str(skey) == 'VLL_L' and str(z) == '150':
                continue
            if animal == 'MD594' and str(skey) == 'VCP_R' and (str(z) == '332' or str(z) == '336'):
                continue
            if animal == 'MD589' and str(skey) == 'RtTg_S' and (str(z) == '220' or str(z) == '222' or str(z) == '223' or str(z) == '240'):
                continue
            if animal == 'MD589' and str(skey) == 'Sp5I_R' and (str(z) == '337'):
                continue
            if animal == 'MD589' and str(skey) == 'VLL_L' and (str(z) == '155'):
                continue
            
            ordering_int = 0

            #20-byte (40 character) random hex string
            segment_id = binascii.hexlify(os.urandom(20)).decode()

            for element in value1:
                x = element[0]
                y = element[1]
                
                insert_into_db(animal, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering_int)

                ordering_int += 1

    print(output)
    # DEBUG INFO: contour for that brain is in aligner.contour_per_structure_per_section