'''
Trimmed down version of the original atlas utilities and also utilities_atlas_lite
'''
import numpy as np
import vtk
import mcubes # https://github.com/pmneila/PyMCubes

from abakit.lib.Controllers.SqlController import SqlController
from abakit.registration.algorithm import umeyama
from abakit.settings import ATLAS
singular_structures = ['AP', '12N', 'RtTg', 'SC', 'IC']
ATLAS = 'atlasV8'


def get_common_structure(brains):
    '''
    Finds the common structures between a brain and the atlas. These are used
    for the inputs to the rigid transformation.
    :param brains: a list (usually just one brain) of brain names
    '''
    sqlController = SqlController('MD594') # just to declare var
    common_structures = set()
    for brain in brains:
        common_structures = common_structures | set(sqlController.get_annotation_points_entry(brain).keys())
    common_structures = list(sorted(common_structures))
    return common_structures


def get_transformation(animal):
    '''
    Fetches the common structures between the atlas and and animal and creates
    the rigid transformation with the umemeya method. Returns the rotation
    and translation matrices.
    :param animal: string of the brain name
    '''
    sqlController = SqlController(animal) # just to declare var
    pointdata = sqlController.get_annotation_points_entry(animal)
    atlas_centers = sqlController.get_annotation_points_entry('Atlas', FK_input_id=1, person_id=16)
    common_structures = get_common_structure(['Atlas', animal])
    point_structures = sorted(pointdata.keys())
    
    dst_point_set = np.array([atlas_centers[s] for s in point_structures if s in common_structures and s in atlas_centers]).T
    point_set = np.array([pointdata[s] for s in point_structures if s in common_structures and s in atlas_centers]).T
    
    R, t = umeyama(point_set, dst_point_set)
    return R, t 


def save_mesh(polydata, filename):
    stlWriter = vtk.vtkSTLWriter()
    stlWriter.SetFileName(filename)
    stlWriter.SetInputData(polydata)
    stlWriter.Write()


def symmetricalize_volume(volume):
    """
    Replace the volume with the average of its left half and right half.
    """
    zcenter = volume.shape[2] // 2
    symmetrical_volume = volume.copy()
    left_half = volume[..., :zcenter]
    right_half = volume[..., -zcenter:]
    left_half_averaged = (left_half + right_half[..., ::-1]) // 2.
    symmetrical_volume[..., :zcenter] = left_half_averaged
    symmetrical_volume[..., -zcenter:] = left_half_averaged[..., ::-1]
    return symmetrical_volume


def volume_to_polygon(volume,origin, times_to_simplify=0,min_vertices=200):
    """
    Convert a volume to a mesh, either as vertices/faces tuple or a vtk.Polydata.

    Args:
        level (float): the level to threshold the input volume
        min_vertices (int): minimum number of vertices. Simplification will stop if the number of vertices drops below this value.
        return_vertex_face_list (bool): If True, return only (vertices, faces); otherwise, return polydata.
    """

    vol_padded = np.pad(volume, ((5,5),(5,5),(5,5)), 'constant') # need this otherwise the sides of volume will not close and expose the hollow inside of structures
    vertices, faces = mcubes.marching_cubes(vol_padded, 0) # more than 5 times faster than skimage.marching_cube + correct_orientation
    vertices = vertices + origin - (5,5,5)
    polydata = mesh_to_polydata(vertices, faces)

    for _ in range(times_to_simplify):
        deci = vtk.vtkQuadricDecimation()
        deci.SetInputData(polydata)
        deci.SetTargetReduction(0.8)
        deci.Update()
        polydata = deci.GetOutput()

        if polydata.GetNumberOfPoints() < min_vertices:
            break
    return polydata
