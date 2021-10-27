import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import io

def get_common_coms(com_dict1,com_dict2):
    landmarks1 = set(com_dict1.keys())
    landmarks2 = set(com_dict2.keys())
    shared_landmarks = landmarks1 & landmarks2
    com1 = [com_dict1[landmarki] for landmarki in shared_landmarks]
    com2 = [com_dict2[landmarki] for landmarki in shared_landmarks]
    return com1,com2,shared_landmarks

def get_trace(com,name):
    marker=dict(size=3)
    com = reshape_com(com)
    trace = go.Scatter3d(x=com[:,0], y=com[:,1],z = com[:,2], 
                    mode='markers',marker = marker, name = name)
    return trace

def get_fig_two_coms(com1,com2,names):
    trace1 = get_trace(com1,names[0])
    trace2 = get_trace(com2,names[1])
    fig = go.Figure()
    fig.add_trace(trace1)
    fig.add_trace(trace2)
    return fig

def get_fig_two_com_dict(com_dict1,com_dict2,names):
    com1,com2,_ = get_common_coms(com_dict1,com_dict2)
    fig = get_fig_two_coms(com1,com2,names)
    return fig

def compare_two_coms(com1,com2,names):
    fig = get_fig_two_coms(com1,com2,names)
    fig.show()

def compare_two_com_dict(com_dict1,com_dict2,names):
    com1,com2,_ = get_common_coms(com_dict1,com_dict2)
    compare_two_coms(com1,com2,names)

def compare_multiple_coms(com_list,name_list):
    assert(len(com_list) == len( name_list))
    ncoms = len(com_list)
    fig = go.Figure()
    for i in range(ncoms):
        tracei = get_trace(com_list[i],name_list[i])
        fig.add_trace(tracei)
    fig.show()

def reshape_com(com1):
    com1 = np.array(com1)
    if com1.shape[1] != 3:
        com1 = com1.T
    return(com1)

def get_fig_compareing_two_com_lists(com_list1,com_list2,name_list1,name_list2,parse_function):
    if type(com_list2) == list:
        assert len(com_list1) == len(com_list2) == len(name_list1) == len(name_list2)
    if type(com_list2) == dict:
        assert len(com_list1) == len(name_list1) == len(name_list2)
    n_pairs = len(com_list1)
    ncols = 2
    nrows = n_pairs//2+1
    subplot_titles = tuple([name_list1[pairi]+' VS ' + name_list2[pairi] for pairi in range(n_pairs)])
    specs = [[{'type': 'Scatter3d'} for _ in range(nrows)] for _ in range(ncols)]
    fig = make_subplots(rows=ncols, cols=nrows,subplot_titles = subplot_titles , specs = specs)
    for i in range(n_pairs):
        rowi = i//nrows 
        coli = i%nrows 
        com1,com2,_= parse_function(com_list1,com_list2,i) 
        trace1 = get_trace(com1,name_list1[i])
        trace2 = get_trace(com2,name_list2[i])
        fig.add_trace(trace1,row = rowi + 1,col = coli + 1)
        fig.add_trace(trace2,row = rowi + 1,col = coli + 1)
    return fig

def get_fig_corresponding_coms_in_two_lists(com_list1,com_list2,name_list1,name_list2):
    identity_parse_function= lambda com1,com2,i : (com1[i],com2[i],None)
    fig = get_fig_compareing_two_com_lists(com_list1,com_list2,name_list1,name_list2,identity_parse_function)
    return fig

def get_fig_corresponding_coms_in_two_dicts(com_dict_list1,com_dict_list2,name_list1,name_list2):
    get_common_coms_two_lists= lambda com1,com2,i : get_common_coms(com1[i],com2[i])
    fig = get_fig_compareing_two_com_lists(com_dict_list1,com_dict_list2,name_list1,name_list2,get_common_coms_two_lists)
    return fig

def get_fig_corresponding_coms_in_dict_to_reference(com_dict_list1,reference,name_list1,name_list2):
    get_common_coms_two_lists= lambda com1,reference,i : get_common_coms(com1[i],reference)
    fig = get_fig_compareing_two_com_lists(com_dict_list1,reference,name_list1,name_list2,get_common_coms_two_lists)
    return fig

def compare_corresponding_coms_in_two_lists(com_list1,com_list2,name_list1,name_list2):
    fig = get_fig_corresponding_coms_in_two_lists(com_list1,com_list2,name_list1,name_list2)
    fig.show()

def compare_corresponding_coms_in_two_dicts(com_dict_list1,com_dict_list2,name_list1,name_list2):
    fig = get_fig_corresponding_coms_in_two_dicts(com_dict_list1,com_dict_list2,name_list1,name_list2)
    fig.show()

def compare_corresponding_coms_in_dict_to_reference(com_dict_list1,reference,name_list1,name_list2):
    fig = get_fig_corresponding_coms_in_dict_to_reference(com_dict_list1,reference,name_list1,name_list2)
    fig.show()

def ploty_to_matplot(fig):
    fig_byte = fig.to_image(format="png", width=1600, height=600)
    fp = io.BytesIO(fig_byte)
    with fp:
        img = mpimg.imread(fp, format='png')
    fig, ax = plt.subplots(1, 1,figsize=(16, 6), dpi=200)
    ax.imshow(img)
    return fig