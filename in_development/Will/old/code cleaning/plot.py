import sys
import numpy as np
import pandas as pd
pipeline_utility_root = '/home/zhw272/programming/pipeline_utility'
sys.path.append(pipeline_utility_root)
from utilities.model.center_of_mass import CenterOfMass
from sql_setup import session
from utilities.sqlcontroller import SqlController
from notebooks.Will.toolbox.IOs.get_landmark_lists import \
    get_shared_landmarks_between_specimens

def query_brain_coms(brain, person_id=28, input_type_id=4):
    # default: person is bili, input_type is aligned
    rows = session.query(CenterOfMass)\
        .filter(CenterOfMass.active.is_(True))\
        .filter(CenterOfMass.prep_id == brain)\
        .filter(CenterOfMass.person_id == person_id)\
        .filter(CenterOfMass.input_type_id == input_type_id)\
        .all()
    row_dict = {}
    for row in rows:
        structure = row.structure.abbreviation
        row_dict[structure] = np.array([row.x, row.y, row.section])
    return row_dict

def get_atlas_centers(
        atlas_box_size=(1000, 1000, 300),
        atlas_box_scales=(10, 10, 20),
        atlas_raw_scale=10
):
    atlas_box_scales = np.array(atlas_box_scales)
    atlas_box_size = np.array(atlas_box_size)
    atlas_box_center = atlas_box_size / 2
    sqlController = SqlController('Atlas')
    # person is lauren, input_type is manual
    atlas_centers = sqlController.get_centers_dict('Atlas', input_type_id=1, person_id=16)

    for structure, center in atlas_centers.items():
        # transform into the atlas box coordinates that neuroglancer assumes
        center = atlas_box_center + np.array(center) * atlas_raw_scale / atlas_box_scales
        atlas_centers[structure] = center

    return atlas_centers

def prepare_table(brains, person_id, input_type_id, save_path):
    df_save = prepare_table_for_save(
        brains,
        person_id=person_id,
        input_type_id=input_type_id
    )
    df_save.to_csv(save_path, index=False)

    df = prepare_table_for_plot(
        brains,
        person_id=person_id,
        input_type_id=input_type_id
    )

    return df_save, df

def get_brain_coms(brains, person_id, input_type_id):
    brain_coms = {}
    for brain in brains:
        brain_coms[brain] = query_brain_coms(
            brain,
            person_id=person_id,
            input_type_id=input_type_id
        )
        # A temporary hack: for ('DK55', corrected), use ('DK55', aligned)
        if (brain, input_type_id) == ('DK55', 2):
            brain_coms[brain] = query_brain_coms(
                brain,
                person_id=person_id,
                input_type_id=4
            )
    return brain_coms

def prepare_table_for_save(brains, person_id, input_type_id):
    atlas_coms = get_atlas_centers()
    brain_coms = get_brain_coms(brains, person_id, input_type_id)
    data = {}
    data['name'] = []
    for s in common_structures:
        for c in ['dx', 'dy', 'dz', 'dist']:
            data['name'] += [f'{s}_{c}']
    for brain in brain_coms.keys():
        data[brain] = []
        offset = [brain_coms[brain][s] - atlas_coms[s]
                  if s in brain_coms[brain] else [np.nan, np.nan, np.nan]
                  for s in common_structures]
        offset = np.array(offset)
        scale = np.array([10, 10, 20])
        dx, dy, dz = (offset * scale).T
        dist = np.sqrt(dx * dx + dy * dy + dz * dz)
        for dx_i, dy_i, dz_i, dist_i in zip(dx, dy, dz, dist):
            data[brain] += [dx_i, dy_i, dz_i, dist_i]
    df = pd.DataFrame(data)

    return df

def get_row(row_type='dx'):
    global dx, dy, dz, dist, structurei
    row = {}
    row['structure'] = common_structures[structurei] + '_' + row_type
    row['value'] = eval(row_type + '[structurei]')
    row['type'] = '_' + row_type
    return row

def prepare_table_for_plot(brains, person_id, input_type_id):
    global dx, dy, dz, dist, structurei
    atlas_coms = get_atlas_centers()
    brain_coms = get_brain_coms(brains, person_id, input_type_id)
    df = pd.DataFrame()
    for brain in brain_coms.keys():
        offset = [brain_coms[brain][s] - atlas_coms[s]
                  if s in brain_coms[brain] else [np.nan, np.nan, np.nan]
                  for s in common_structures]
        offset = np.array(offset)
        scale = np.array([10, 10, 20])
        dx, dy, dz = (offset * scale).T
        dist = np.sqrt(dx * dx + dy * dy + dz * dz)

        df_brain = pd.DataFrame()

        n_structures = len(common_structures)
        for structurei in range(n_structures):
            row = get_row('dx')
            print(row)
            df_brain = df_brain.append(pd.DataFrame(row,index=[0]), ignore_index=True)
            row = get_row('dy')
            df_brain = df_brain.append(pd.DataFrame(row,index=[0]), ignore_index=True)
            row = get_row('dz')
            df_brain = df_brain.append(pd.DataFrame(row,index=[0]), ignore_index=True)
            row = get_row('dist')
            df_brain = df_brain.append(pd.DataFrame(row,index=[0]), ignore_index=True)

        df_brain['brain'] = brain
        df = df.append(df_brain, ignore_index=True)
    return df

brains_to_extract_common_structures = ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']
brains_to_examine = ['DK39', 'DK41', 'DK43', 'DK52', 'DK54', 'DK55']

common_structures = get_shared_landmarks_between_specimens(brains_to_extract_common_structures)

df_save, df = prepare_table(
    brains_to_examine,
    person_id=28,
    input_type_id=4,
    save_path=pipeline_utility_root+'/notebooks/Bili/data/rigid-alignment-error.csv'
)
df.head()