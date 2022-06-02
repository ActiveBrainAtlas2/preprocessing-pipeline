from lib.Controllers.SqlController import SqlController
import pickle
from Plotter.Plotter import Plotter
import numpy as np
from lib.Transformation import Transformation
import SimpleITK as sitk

source = 'DK39'
destination = 'Atlas'
plotter = Plotter()
controller = SqlController('Atlas')
transformation = controller.get_transformation_row(source = source,destination = destination, transformation_type = 4)
rigid_transform = pickle.loads(transformation.transformation)
brain_com = controller.get_layer_data_entry(source)
atlas_com = controller.get_atlas_centers()
common_keys = atlas_com.keys() & brain_com.keys()

dst_point_set = np.array([atlas_com[s] for s in common_keys]).T
src_point_set = np.array([brain_com[s] for s in common_keys]).T

tf = rigid_transform.forward_transform_points(src_point_set)

plotter.compare_3d_point_sets([src_point_set.T,dst_point_set.T,tf.T],['src','dst','tf'])

print(transformation)