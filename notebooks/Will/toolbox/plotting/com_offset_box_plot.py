import numpy as np
import pandas as pd
from notebooks.Will.toolbox.rough_alignment.diagnostics import get_common_land_marks
from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
from notebooks.Will.toolbox.IOs.get_plot_save_path import get_plot_save_path
import plotly.express as px

def get_fig(offsets,title = ''):
    df_manual = prepare_table_for_plot(offsets)
    fig = px.scatter(df_manual, x="structure", y="value", color="type", hover_data=['brain'],title = title)
    return fig

def plot_offsets(offsets,title = ''):
    fig = get_fig(offsets,title = title)
    fig.show()

def save_offsets(offsets,file_name,folder,title = ''):
    fig = get_fig(offsets,title = title)
    save_path = get_plot_save_path(folder = folder,file_name = file_name)
    fig.write_html(save_path)

def prepare_table_for_plot(offsets):
    prep_list = get_prep_list_for_rough_alignment_test()
    common_landmarks = get_common_land_marks()
    df = pd.DataFrame()
    prepi = 0
    for offset in offsets:
        offset = np.array(offset)
        dx, dy, dz = offset.T
        dist = np.sqrt(dx * dx + dy * dy + dz * dz)
        df_brain = pd.DataFrame()
        for data_type in ['dx','dy','dz','dist']:
            data = {}
            data['structure'] = common_landmarks
            data['value'] = eval(data_type)
            data['type'] = data_type
            df_brain = df_brain.append(pd.DataFrame(data), ignore_index=True)
        df_brain['brain'] = prep_list[prepi]
        df = df.append(df_brain, ignore_index=True)
        prepi+=1
    return df