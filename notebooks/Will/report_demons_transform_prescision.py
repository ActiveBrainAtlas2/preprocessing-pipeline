import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from sqlalchemy import func

sns.set_style("whitegrid")

PIPELINE_ROOT = Path('.').absolute().parents[2]
sys.path.append(PIPELINE_ROOT.as_posix())
from utilities.model.center_of_mass import CenterOfMass
from utilities.model.structure import Structure
from sql_setup import session

# configurations for brains
brains_to_extract_common_structures = ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']
brains_to_examine = ['DK39', 'DK41', 'DK43', 'DK52', 'DK54', 'DK55']

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

from utilities.sqlcontroller import SqlController

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

atlas_coms = get_atlas_centers()

common_structures = set()
for brain in brains_to_extract_common_structures:
    common_structures = common_structures | set(query_brain_coms(brain).keys())
common_structures = list(sorted(common_structures))
common_structures

def plot(df, ymin, ymax, ystep, title):
    fig, ax = plt.subplots(2, 1, figsize=(16, 12), dpi=200)
    
    sns.boxplot(ax=ax[0], x="structure", y="value", hue="type", data=df)
    ax[0].xaxis.grid(True)
    ax[0].set_xlabel('Structure')
    ax[0].set_ylabel('um')
    ax[0].set_title('full dynamic range')
    
    sns.boxplot(ax=ax[1], x="structure", y="value", hue="type", data=df)
    ax[1].xaxis.grid(True)
    ax[1].set_ylim(ymin, ymax)
    ax[1].yaxis.set_ticks(np.arange(ymin, ymax + 1, ystep))
    ax[0].set_xlabel('Structure')
    ax[1].set_ylabel('um')
    ax[1].set_title('zoom in')
    
    fig.suptitle(title, y=0.92)
    plt.show()
    return fig

figs = []