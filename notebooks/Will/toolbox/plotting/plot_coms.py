import plotly.graph_objects as go
import numpy as np

def compare_two_coms(com1,com2,names):
    com1 = reshape_com(com1)
    com2 = reshape_com(com2)
    name1,name2 = names
    marker=dict(size=3)
    fig = go.Figure(data=go.Scatter3d(x=com1[:,0], y=com1[:,1],z = com1[:,2], 
                    mode='markers',marker = marker,  name = name1))
    fig.add_trace(go.Scatter3d(x=com2[:,0], y=com2[:,1],z = com2[:,2], 
                    mode='markers',marker = marker, name = name2))
    fig.show()

def reshape_com(com1):
    com1 = np.array(com1)
    if com1.shape[1] != 3:
        com1 = com1.T
    return(com1)