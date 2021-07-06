import numpy as np
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

def plot_offset_between_two_com_sets(com1,com2,prep_list_function,landmark_list_function,title):
    offset_table = get_offset_table_from_two_com_sets(com1,com2,prep_list_function,landmark_list_function)
    plot_offset_box(offset_table, title = title)

def plot_offset_from_offset_arrays(offsets,prep_list_function,landmark_list_function,title):
    offset_table = get_offset_table_from_offset_array(offsets,prep_list_function,landmark_list_function)
    plot_offset_box(offset_table, title = title)

def plot_offset_from_coms_to_a_reference(coms,reference,prep_list_function,landmark_list_function,title):
    offset_table = get_offset_table_from_coms_to_a_reference(coms,reference,prep_list_function,landmark_list_function)
    plot_offset_box(offset_table, title = title)

def get_fig_offset_between_two_com_sets(com1,com2,prep_list_function,landmark_list_function,title):
    offset_table = get_offset_table_from_two_com_sets(com1,com2,prep_list_function,landmark_list_function)
    fig = get_fig_offset_box(offset_table, title = title)
    return fig

def get_fig_offset_from_offset_arrays(offsets,prep_list_function,landmark_list_function,title):
    offset_table = get_offset_table_from_offset_array(offsets,prep_list_function,landmark_list_function)
    fig = get_fig_offset_box(offset_table, title = title)
    return fig

def get_fig_offset_from_coms_to_a_reference(coms,reference,prep_list_function,landmark_list_function,title):
    offset_table = get_offset_table_from_coms_to_a_reference(coms,reference,prep_list_function,landmark_list_function)
    fig = get_fig_offset_box(offset_table, title = title)
    return fig

def get_offset_table_from_coms_to_a_reference(coms,reference,prep_list_function,landmark_list_function):
    offset_table = get_offset_table(coms,reference,prep_list_function,landmark_list_function,get_offseti_from_com_list_and_reference)
    return offset_table

def get_offset_table_from_two_com_sets(com1,com2,prep_list_function,landmark_list_function):
    offset_table = get_offset_table(com1,com2,prep_list_function,landmark_list_function,get_offseti_from_two_com_lists)
    return offset_table
    
def get_offset_table_from_offset_array(offsets,prep_list_function,landmark_list_function):
    offset_function = lambda offsets,no_comparison_needed,no_landmark_list_needed,comi : offsets[comi]
    offset_table = get_offset_table(offsets,None,prep_list_function,landmark_list_function,offset_function)
    return offset_table

def get_offset_table(com1,com2,prep_list_function,landmark_list_function,offset_function):
    # if type(com2) == list:
    #     breakpoint()
    prep_list = prep_list_function()
    landmarks = landmark_list_function(prep_list)
    offset_table = pd.DataFrame()
    prepi = 0
    for comi in range(len(com1)):
        offset = offset_function(com1,com2,landmarks,comi)
        offset_table_entry = get_offset_table_entry(offset,landmarks)
        offset_table_entry['brain'] = prep_list[prepi]
        offset_table = offset_table.append(offset_table_entry, ignore_index=True)
        prepi+=1
    return offset_table

def get_offseti_from_com_list_and_reference(coms,reference,landmarks,comi):
    offset = [coms[comi][s] - reference[s]
                  if s in coms[comi] and s in reference  else [np.nan, np.nan, np.nan]
                  for s in landmarks]
    return offset

def get_offseti_from_two_com_lists(com1,com2,landmarks,comi):
    offset = [com1[comi][s] - com2[comi][s]
                  if s in com1[comi] and s in com2[comi] else [np.nan, np.nan, np.nan]
                  for s in landmarks]
    return offset

def get_offset_table_entry(offset,landmarks):
    offset = np.array(offset)
    dx, dy, dz = offset.T
    dist = np.sqrt(dx * dx + dy * dy + dz * dz)
    df_brain = pd.DataFrame()
    for data_type in ['dx','dy','dz','dist']:
        data = {}
        data['structure'] = landmarks
        data['value'] = eval(data_type)
        data['type'] = data_type
        df_brain = df_brain.append(pd.DataFrame(data), ignore_index=True)
    return df_brain

def get_fig_offset_box(offsets_table, title = ''):
    fig, ax = plt.subplots(1, 1, figsize=(16, 6), dpi=200)
    sns.boxplot(ax=ax, x="structure", y="value", hue="type", data=offsets_table)
    ax.xaxis.grid(True)
    ax.set_xlabel('Structure')
    ax.set_ylabel('um')
    ax.set_title(title)
    return fig
    
def plot_offset_box(offsets_table, title = ''):
    fig = get_fig_offset_box(offsets_table, title = '')
    plt.show()
