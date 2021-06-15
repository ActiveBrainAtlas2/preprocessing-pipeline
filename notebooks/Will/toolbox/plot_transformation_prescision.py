import seaborn as sns
import matplotlib.pyplot as plt
sns.set_style("whitegrid")
import SimpleITK as sitk
from notebooks.Will.toolbox.data_base.sql_tools import get_atlas_centers
from notebooks.Will.toolbox.brain_and_structure_info import get_common_structures,get_list_of_brains_to_align
import pandas as pd
import numpy as np

def get_demon_transformed_com(braini = 'DK39'):
    import json
    with open('/home/zhw272/programming/pipeline_utility/notebooks/Bili/data/DK52_coms_kui_detected.json', 'r') as f:
        moving_com = json.load(f)
    save_path = '/net/birdstore/Active_Atlas_Data/data_root/tfm'
    transform = sitk.ReadTransform(save_path + '/demons/' + braini + '_demons.tfm')
    fixed_coms = {}
    for name, com in moving_com.items():
        fixed_coms[name] = transform.TransformPoint(com)
    return fixed_coms

def prepare_table_for_plot():
    brains_to_examine = get_list_of_brains_to_align()
    brain_coms = {}
    for braini in brains_to_examine:
        brain_coms[braini] = get_demon_transformed_com(braini)
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