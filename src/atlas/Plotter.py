import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
from matplotlib.widgets import Slider

class Plotter:
    def plot_contours(self,contours):
        data = []
        for sectioni in contours:
            datai = np.array(contours[sectioni])
            npoints = datai.shape[0]
            datai = np.hstack((datai,np.ones(npoints).reshape(npoints,1)*sectioni))
            data.append(datai)
        data = np.vstack(data)
        fig = go.Figure(data=[go.Scatter3d(x=data[:,0], y=data[:,1], z=data[:,2],mode='markers')])
        fig.show()
    
    def plot_3d_boolean_array(self,boolean_array):
        ax = plt.figure().add_subplot(projection='3d')
        ax.voxels(boolean_array,edgecolor='k')
        plt.show()
    
    def plot_3d_image_stack(self,stack,axis = 0):
        if axis !=0:
            stack = np.swapaxes(stack,0,axis)
        def _update_image(val):
            current_section = slider.val
            plot.set_data(stack[int(current_section)])
            fig.canvas.draw_idle()
        fig, ax = plt.subplots()
        mid_point = int(len(stack)/2)
        plot = ax.imshow(stack[mid_point])
        ax = plt.axes([0.25, 0.15, 0.65, 0.03])
        slider = Slider(ax, 'index', 0, stack.shape[0], valinit=mid_point, valfmt='%d')
        slider.on_changed(_update_image)
        plt.show()
    
    def compare_point_dictionaries(self,point_dicts):
        fig = make_subplots(rows = 1, cols = 1,specs=[[{'type':'scatter3d'}]])
        for point_dict in point_dicts:
            values = np.array(list(point_dict.values()))
            fig.add_trace(go.Scatter3d(x=values[:,0], y=values[:,1], z=values[:,2],
                                    mode='markers'),row = 1,col = 1)
        fig.show()