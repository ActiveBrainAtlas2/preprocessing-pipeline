from Registration.PointSetRegistration.PointSetAlignment import \
    get_rigid_alignmented_points, get_affine_alignment_points, get_similarity_alignment_points
from lib.SqlController import SqlController
from atlas.Plotter import Plotter
import numpy as np
from abakit.registration.utilities import get_and_apply_similarity_transform_to_dictionaries


plotter = Plotter()
controller = SqlController('DK52')
com52 = controller.get_com_dict('DK52')
com55 = controller.get_com_dict('DK55')

rigid_aligned = np.array(list(get_rigid_alignmented_points(com55, com52).values()))
affine_aligned = np.array(list(get_affine_alignment_points(com55, com52).values()))

sim_aligned_itk = get_similarity_alignment_points(com55, com52)
sim_aligned_uemeda = get_and_apply_similarity_transform_to_dictionaries(moving=com52,fixed =com55)

plotter.compare_3d_point_sets([np.array(list(sim_aligned_itk.values())),
np.array(list(sim_aligned_uemeda.values())),np.array(list(com55.values()))],['itk','uemeda','fixed'])
