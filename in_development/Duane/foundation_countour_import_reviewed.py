'''
IMPORT FOUNDATION BRAIN IMAGES' VERTICIES INTO DB

CREATED: 16-MAR-2022
LAST EDIT: 16-MAR-2022
AUTHORS: DUANE RINEHART

SECONDARY IMPORT OF ANNOTATIONS (REVIEWED)

'''

import os
import re
import sys
import binascii # unique segment id (contour) ref: https://github.com/google/neuroglancer/blob/master/python/neuroglancer/random_token.py
import pandas as pd

#WORKAROUND FOR PYTHONPATH
src='/net/birdstore/common_programming/pipeline_utility/src'
sys.path.append(src)


# FOR SAVE TO DB
from pipeline.lib.sql_setup import session
from model.structure import Structure


dest_db_schema = 'dev2_test'
out_path = "/net/birdstore/drinehart/img_compare/"
src_contours = os.path.join(out_path, "compare_v2.xlsx")


# DEFAULTS
FK_owner_id = '4' #ALL OWNED BY USER 'dk'
FK_input_id = '1' #ALL MANUAL
active = '1'


def load_contours():
    '''LOAD IN DUPLICATED (POTENTIALY) SETS OF CONTOURS (POINTS)'''
    in_contours = pd.read_excel(
        os.path.join(src_contours),
        engine='openpyxl',
    )
    return in_contours[['MOUSE', 'SECTION', 'STRUCTURE', 'STRUCTURE_ID', 'GOOD']] 



def insert_into_db(prep_id, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering_int):

    sql_statement = f'INSERT INTO {dest_db_schema}.annotations_points (prep_id, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering) VALUES (\'{prep_id}\',\'{FK_structure_id}\', \'{FK_owner_id}\', \'{FK_input_id}\', \'{label}\',  \'{x}\', \'{y}\', \'{z}\', \'{active}\', \'{segment_id}\', \'{ordering_int}\')'
    print(sql_statement)
    # session.execute(sql_statement)
    # session.commit()


def parse_contours(contours1):
    #print(index, row['MOUSE'], row['SECTION'], row['STRUCTURE'], row['GOOD']) - DEBUG: SRC LAYOUT
    print("PROGRESS", 'MOUSE', 'SECTION', 'STRUCTURE', 'GOOD', sep=" : ")
    for index, row in contours1.iterrows():

        print("CURRENT- ", row['MOUSE'], row['SECTION'], row['STRUCTURE'], row['STRUCTURE_ID'], sep=" : ")

        #***PARSE X,Y VALUES (VERTICES)***
        #REMOVE BRACKETS FROM STRING
        lstcontour_points1 = re.sub(r"[\([{})\]]", '', row['GOOD']).split("\n")

        lstpairs1 = []
        #LIST OF TUPLES - EACH TUPLE HAS X,Y POINTS
        for pairs in lstcontour_points1:
            lstpair = list(filter(str.strip,pairs.split(" "))) #REMOVE STRINGS ELEMENTS THAT ONLY CONTAIN WHITESPACE (NULL) FROM LIST
            pair = (float(lstpair[0]), float(lstpair[1]))
            lstpairs1.append(pair)

        animal = row['MOUSE']
        label = row['STRUCTURE']
        FK_structure_id = row['STRUCTURE_ID']
        ordering_int = 0
        #20-byte (40 character) random hex string
        segment_id = binascii.hexlify(os.urandom(20)).decode()
        z = row['SECTION']
        for tpl_coord in lstpairs1:
            x = tpl_coord[0]
            y = tpl_coord[1]
                
            #print(animal, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering_int)
            insert_into_db(animal, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering_int)

            ordering_int += 1


        #create_plot(row['MOUSE'], row['SECTION'], row['STRUCTURE'], lstpairs1, lstpairs2)

        #DEBUG:
        #if row['MOUSE'] == 'MD589':
        #    create_plot(row['MOUSE'], row['SECTION'], row['STRUCTURE'], lstpairs1, lstpairs2)
        
    return 'done'


# def get_structure_table_correspondance():
#     rows = session.query(Structure).all()
#     results = {}
#     for row in rows:
#         results[row.abbreviation] = [row.id, row.description]
#     return results


# #SINGLE QRY TO GET STRUCTURE DATA
# structure_data = get_structure_table_correspondance()


contours = load_contours()
print("LOG:")
parse_contours(contours)


# for animal in animals:
#     aligner = FoundationContourAligner(animal, atlas='atlasV8')
#     aligner.load_contours_for_Foundation_brains()

#     # FOR DEBUG 
#     # df = pd.DataFrame.from_dict(aligner.contour_per_structure_per_section)
#     # df.to_csv(f"/home/drinehart/out_no_densify_{animal}.csv")

#     output = ""
#     for skey, value in aligner.contour_per_structure_per_section.items():

#         output += f"DEBUG - [{animal}] (structure):" + str(skey) + "; QTY:" + str(len(value)) + "\n"
#         #print("DEBUG - (section):", skey, "; QTY:", len(value))
#         #pull FK_structure_id from structure table (in db) where abbreviation = structure name (key)
#         FK_structure_data = structure_data.get(skey) #LOOKUP STRUCTURE ID
#         FK_structure_id = FK_structure_data[0]
#         label = FK_structure_data[1]
        

#         ordering_int = 0
#         for z, value1 in value.items():

#             # FILTER PROBLEMATIC SETS *WILL ADD LATER
#             if animal == 'MD594' and str(skey) == 'VLL_R' and (str(z) == '300' or str(z) == '308'):
#                 continue
#             if animal == 'MD594' and str(skey) == 'VLL_L' and str(z) == '150':
#                 continue
#             if animal == 'MD594' and str(skey) == 'VCP_R' and (str(z) == '332' or str(z) == '336'):
#                 continue
#             if animal == 'MD589' and str(skey) == 'RtTg_S' and (str(z) == '220' or str(z) == '222' or str(z) == '223' or str(z) == '240'):
#                 continue
#             if animal == 'MD589' and str(skey) == 'Sp5I_R' and (str(z) == '337'):
#                 continue
#             if animal == 'MD589' and str(skey) == 'VLL_L' and (str(z) == '155'):
#                 continue
                
#             #20-byte (40 character) random hex string
#             segment_id = binascii.hexlify(os.urandom(20)).decode()

#             for element in value1:
#                 x = element[0]
#                 y = element[1]
                
#                 #insert_into_db(animal, FK_structure_id, FK_owner_id, FK_input_id, label, x, y, z, active, segment_id, ordering_int)

#                 ordering_int += 1

#     print(output)
    # DEBUG INFO: contour for that brain is in aligner.contour_per_structure_per_section