import numpy as np
from utilities.model.center_of_mass import CenterOfMass
from sql_setup import session
from utilities.sqlcontroller import SqlController
import pandas as pd
import sys
from pathlib import Path
from notebooks.Will.toolbox.brain_and_structure_info import get_list_of_brains_to_align
PIPELINE_ROOT = Path('.').absolute().parents[2]
sys.path.append(PIPELINE_ROOT.as_posix())

def get_common_structures():
    brains_to_align = get_list_of_brains_to_align()
    common_structures = set()
    for brain in brains_to_align:
        common_structures = common_structures | set(query_brain_coms(brain).keys())
    common_structures = list(sorted(common_structures))
    return common_structures

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

def query_brain_coms(brain, person_id=28, input_type_id=4):
    rows = session.query(CenterOfMass)\
        .filter(CenterOfMass.active.is_(True))\
        .filter(CenterOfMass.prep_id == brain)\
        .filter(CenterOfMass.person_id == person_id)\
        .filter(CenterOfMass.input_type_id == input_type_id)\
        .all()
    brain_centers = {}
    for row in rows:
        structure = row.structure.abbreviation
        brain_centers[structure] = np.array([row.x, row.y, row.section])
    return brain_centers



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
    brain_coms = get_brain_coms(brains, person_id, input_type_id)
    common_structures = get_common_structures()
    atlas_coms = get_atlas_centers()
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


def prepare_table_for_plot(brains, person_id, input_type_id):
    brain_coms = get_brain_coms(brains, person_id, input_type_id)
    common_structures = get_common_structures()
    atlas_coms = get_atlas_centers()
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

        data = {}
        data['structure'] = common_structures
        data['value'] = dx
        data['type'] = 'dx'
        df_brain = df_brain.append(pd.DataFrame(data), ignore_index=True)

        data = {}
        data['structure'] = common_structures
        data['value'] = dy
        data['type'] = 'dy'
        df_brain = df_brain.append(pd.DataFrame(data), ignore_index=True)

        data = {}
        data['structure'] = common_structures
        data['value'] = dz
        data['type'] = 'dz'
        df_brain = df_brain.append(pd.DataFrame(data), ignore_index=True)

        data = {}
        data['structure'] = common_structures
        data['value'] = dist
        data['type'] = 'dist'
        df_brain = df_brain.append(pd.DataFrame(data), ignore_index=True)

        df_brain['brain'] = brain
        df = df.append(df_brain, ignore_index=True)
    return df