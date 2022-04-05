import os
import sys
import numpy as np
import vtk
#from vtk.util import numpy_support
import mcubes # https://github.com/pmneila/PyMCubes
from vtkmodules.util import numpy_support

from lib.file_location import DATA_PATH
SECTION_THICKNESS = 20. # in um

REGISTRATION_PARAMETERS_ROOTDIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL/CSHL_registration_parameters'

MESH_DIR = os.path.join(DATA_PATH, 'CSHL_meshes')
VOL_DIR = os.path.join(DATA_PATH, 'CSHL', 'CSHL_volumes')
ATLAS = 'atlasV8'
paired_structures = ['5N', '6N', '7N', '7n', 'Amb',
                     'LC', 'LRt', 'Pn', 'Tz', 'VLL', 'RMC',
                     'SNC', 'SNR', '3N', '4N', 'Sp5I',
                     'Sp5O', 'Sp5C', 'PBG', '10N', 'VCA', 'VCP', 'DC']
singular_structures = ['AP', '12N', 'RtTg', 'SC', 'IC']
singular_structures_with_side_suffix = ['AP_S', '12N_S', 'RtTg_S', 'SC_S', 'IC_S']
all_known_structures = paired_structures + singular_structures


def mesh_to_polydata(vertices, faces, num_simplify_iter=0, smooth=False):
    """
    Args:
        vertices ((num_vertices, 3) arrays)
        faces ((num_faces, 3) arrays)
    """
    polydata = vtk.vtkPolyData()
    points = vtk.vtkPoints()
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("Colors")
    colors.SetNumberOfTuples(len(faces))

    for pointi, (x,y,z) in enumerate(vertices):
        points.InsertPoint(pointi, x, y, z)

    if len(faces) > 0:
        cells = vtk.vtkCellArray()
        cell_arr = np.empty((len(faces)*4, ), np.int)
        cell_arr[::4] = 3
        cell_arr[1::4] = faces[:,0]
        cell_arr[2::4] = faces[:,1]
        cell_arr[3::4] = faces[:,2]
        cell_vtkArray = numpy_support.numpy_to_vtkIdTypeArray(cell_arr, deep=1)
        cells.SetCells(len(faces), cell_vtkArray)
        colors.InsertNextTuple3(255,255,0)

    polydata.SetPoints(points)

    if len(faces) > 0:
        polydata.SetPolys(cells)
        polydata.GetCellData().SetScalars(colors)
        polydata = simplify_polydata(polydata, num_simplify_iter, smooth)
    else:
        sys.stderr.write('mesh_to_polydata: No faces are provided, so skip simplification.\n')

    return polydata

def simplify_polydata(polydata, num_simplify_iter=0, smooth=False):
    for simplify_iter in range(num_simplify_iter):
        deci = vtk.vtkQuadricDecimation()
        deci.SetInputData(polydata)
        deci.SetTargetReduction(0.8)
        # 0.8 means each iteration causes the point number to drop to 20% the original
        deci.Update()
        polydata = deci.GetOutput()

        if smooth:
            smoother = vtk.vtkWindowedSincPolyDataFilter()
    #         smoother.NormalizeCoordinatesOn()
            smoother.SetPassBand(.1)
            smoother.SetNumberOfIterations(20)
            smoother.SetInputData(polydata)
            smoother.Update()
            polydata = smoother.GetOutput()

        if polydata.GetNumberOfPoints() < 200:
            break

    return polydata

def polydata_to_mesh(polydata):
    """
    Extract vertice and face data from a polydata object.

    Returns:
        (vertices, faces)
    """

    vertices = np.array([polydata.GetPoint(i) for i in range(polydata.GetNumberOfPoints())])

    try:
        face_data_arr = numpy_support.vtk_to_numpy(polydata.GetPolys().GetData())

        faces = np.c_[face_data_arr[1::4],
                      face_data_arr[2::4],
                      face_data_arr[3::4]]
    except:
        sys.stderr.write('polydata_to_mesh: No faces are loaded.\n')
        faces = []

    return vertices, faces

def get_original_volume_basename_v2(stack_spec):
    """
    Args:
        stack_spec (dict):
            - prep_id
            - detector_id
            - vol_type
            - structure (str or list)
            - name
            - resolution
    """

    if 'prep_id' in stack_spec:
        prep_id = stack_spec['prep_id']
    else:
        prep_id = None

    if 'detector_id' in stack_spec:
        detector_id = stack_spec['detector_id']
    else:
        detector_id = None

    if 'vol_type' in stack_spec:
        volume_type = stack_spec['vol_type']
    else:
        volume_type = None

    if 'structure' in stack_spec:
        structure = stack_spec['structure']
    else:
        structure = None

    assert 'name' in stack_spec, stack_spec
    stack = stack_spec['name']

    if 'resolution' in stack_spec:
        resolution = stack_spec['resolution']
    else:
        resolution = None

    components = []
    if prep_id is not None:
        if isinstance(prep_id, str):
            components.append(prep_id)
        elif isinstance(prep_id, int):
            components.append('prep%(prep)d' % {'prep': prep_id})
    if detector_id is not None:
        components.append('detector%(detector_id)d' % {'detector_id': int(detector_id)})
    if resolution is not None:
        components.append(resolution)

    tmp_str = '_'.join(components)
    basename = '%(stack)s_%(tmp_str)s%(volstr)s' % \
               {'stack': stack, 'tmp_str': (tmp_str + '_') if tmp_str != '' else '',
                'volstr': volume_type_to_str(volume_type)}
    if structure is not None:
        if isinstance(structure, str):
            basename += '_' + structure
        elif isinstance(structure, list):
            basename += '_' + '_'.join(sorted(structure))
        else:
            raise ValueError('The following structure is not valid: ', structure)
    return basename

def mirror_volume_v2(volume, new_centroid, centroid_wrt_origin=None):
    """
    Use to get the mirror image of the volume.
    `Volume` argument is the volume in right hemisphere.
    Note: This assumes the mirror plane is vertical; Consider adding a mirror plane as argument
    Args:
        volume: any representation
        new_centroid: the centroid of the resulting mirrored volume.
        centroid_wrt_origin: if not specified, this uses the center of mass.
    Returns:
        (volume, origin): new origin is wrt the same coordinate frame as `new_centroid`.
    """

    vol, ori = convert_volume_forms(volume=volume, out_form=("volume", "origin"))
    ydim, xdim, zdim = vol.shape
    if centroid_wrt_origin is None:
        centroid_wrt_origin = get_centroid_3d(vol)
    centroid_x_wrt_origin, centroid_y_wrt_origin, centroid_z_wrt_origin = centroid_wrt_origin
    new_origin_wrt_centroid = (-centroid_x_wrt_origin, -centroid_y_wrt_origin, - (zdim - 1 - centroid_z_wrt_origin))

    new_origin = new_centroid + new_origin_wrt_centroid
    new_vol = vol[:,:,::-1].copy()
    return new_vol, new_origin