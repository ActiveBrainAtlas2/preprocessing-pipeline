from Registration.point_set_alignment.PointSetAlignment import \
    get_rigid_alignmented_points, get_affine_alignment_points
from lib.sqlcontroller import SqlController
from atlas.Plotter import Plotter
import numpy as np
plotter = Plotter()
controller = SqlController('DK52')
com52 = controller.get_com_dict('DK52')
com55 = controller.get_com_dict('DK55')

rigid_aligned = np.array(list(get_rigid_alignmented_points(com55, com52).values()))
affine_aligned = np.array(list(get_affine_alignment_points(com55, com52).values()))
plotter.compare_3d_point_sets([rigid_aligned,affine_aligned,np.array(list(com55.values()))],
['rigid','affine','fixed'])
