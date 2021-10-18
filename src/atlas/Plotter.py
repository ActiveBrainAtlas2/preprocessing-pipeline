import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
from matplotlib.widgets import Slider

class Plotter:

    def set_show_as_true(self):
        self.show = True
    
    def set_show_as_false(self):
        self.show = False

    def get_contour_data(self,contours,down_sample_factor = 10):
        data = []
        for sectioni in contours:
            datai = np.array(contours[sectioni])
            datai = datai[::down_sample_factor,:]
            npoints = datai.shape[0]
            datai = np.hstack((datai,np.ones(npoints).reshape(npoints,1)*int(sectioni)))
            data.append(datai)
        data = np.vstack(data)
        return data
    
    def plot_3d_scatter(self,data,marker={},title = ''):
        fig = go.Figure(data=[go.Scatter3d(x=data[:,0], y=data[:,1], z=data[:,2],mode='markers',marker=marker)])
        fig.update_layout(title=title)
        fig.show()

    def plot_contours(self,contours):
        data = self.get_contour_data(contours)
        self.plot_3d_scatter(data)
    
    def plot_3d_boolean_array(self,boolean_array):
        ax = plt.figure().add_subplot(projection='3d')
        ax.voxels(boolean_array,edgecolor='k')
        self.show_according_to_setting()
    
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
        self.show_according_to_setting()

    def compare_contour_and_stack(self,contour,stack,axis = 2):
        if axis !=0:
            stack = np.swapaxes(stack,0,axis)

        def get_contouri(sectioni):
            min = np.min([np.min(contouri,0) for contouri in contour],axis=0)
            contouri = np.array(contour[sectioni])
            contouri = contouri - min
            return contouri

        def _update_image(val):
            current_section = slider.val
            sectioni = int(current_section) 
            image.set_data(stack[sectioni])
            contouri = get_contouri(sectioni)
            scatter.set_offsets(contouri)
            fig.canvas.draw_idle()
        fig, ax = plt.subplots()
        mid_point = int(len(stack)/2)
        image = ax.imshow(stack[mid_point])
        contouri = get_contouri(mid_point)
        scatter = ax.scatter(contouri[:,0],contouri[:,1])
        ax = plt.axes([0.25, 0.15, 0.65, 0.03])
        slider = Slider(ax, 'index', 0, stack.shape[0]-1, valinit=mid_point, valfmt='%d')
        slider.on_changed(_update_image)
        self.show_according_to_setting()
    
    def imshow(self,img):
        plt.imshow(img)
        self.show_according_to_setting()
        
    def plot_contour(self,contour):
        if contour.shape[0] ==2:
            contour = contour.T
        plt.scatter(contour[:,0],contour[:,1])
        self.show_according_to_setting()

    def show_according_to_setting(self):
        if hasattr(self,'show'):
            if self.show:
                plt.show()
        else:
            plt.show()
    
    def show():
        plt.show()

    def compare_point_dictionaries(self,point_dicts):
        fig = make_subplots(rows = 1, cols = 1,specs=[[{'type':'scatter3d'}]])
        for point_dict in point_dicts:
            values = np.array(list(point_dict.values()))
            fig.add_trace(go.Scatter3d(x=values[:,0], y=values[:,1], z=values[:,2],
                                    mode='markers'),row = 1,col = 1)
        fig.show()