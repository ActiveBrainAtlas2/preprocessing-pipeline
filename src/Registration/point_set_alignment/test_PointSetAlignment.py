from Registration.point_set_alignment.PointSetAlignment import get_rigid_alignment, get_affine_alignment
from lib.sqlcontroller import SqlController
from atlas.Plotter import Plotter
import numpy as np
plotter = Plotter()
controller = SqlController('DK52')
com52 = controller.get_com_dict('DK52')
com55 = controller.get_com_dict('DK55')
shared_keys = set(com52.keys()).intersection(set(com55.keys()))
com52 = np.array([com52[key] for key in shared_keys])
com55 = np.array([com55[key] for key in shared_keys])

rigid_aligned = get_rigid_alignment(fixed = com55, moving = com52)
affine_aligned = get_affine_alignment(fixed = com55, moving = com52)
plotter.compare_3d_point_sets([rigid_aligned,affine_aligned,np.array(com55)],['rigid','affine','fixed'])
