import os
import sys
import time
import matplotlib.pyplot as plt
import numpy as np
from pandas import read_hdf
from skimage import io, img_as_ubyte
import json
from collections import defaultdict
import re
from skimage.measure import find_contours, regionprops
from skimage.filters import gaussian
from scipy.ndimage.morphology import distance_transform_edt
from skimage.morphology import closing, disk
from scipy.ndimage.morphology import binary_closing
import pickle
import vtk
#from vtk.util import numpy_support
import mcubes # https://github.com/pmneila/PyMCubes
from skimage.transform import resize
from vtkmodules.util import numpy_support
from pathlib import Path

#PIPELINE_ROOT = Path('.').absolute().parent
#sys.path.append(PIPELINE_ROOT.as_posix())
from lib.sqlcontroller import SqlController
from lib.utilities_alignment import load_hdf, one_liner_to_arr, convert_resolution_string_to_um
from lib.file_location import FileLocationManager, DATA_PATH
from lib.coordinates_converter import CoordinatesConverter
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


def find_merged_bounding_box(bounding_box=None):
    bounding_box = np.array(bounding_box)
    xmin, ymin, zmin = np.min(bounding_box[:, [0,2,4]], axis=0)
    xmax, ymax, zmax = np.max(bounding_box[:, [1,3,5]], axis=0)
    bbox = xmin, xmax, ymin, ymax, zmin, zmax
    return bbox

def crop_and_pad_volume(volumes, bounding_box, merged_bounding_box):
    """
    Crop and pad an volume.
    in_vol and in_bbox together define the input volume in a underlying space.
    out_bbox then defines how to crop the underlying space, which generates the output volume.
    Args:
        in_bbox ((6,) array): the bounding box that the input volume is defined on. If None, assume origin is at (0,0,0) of the input volume.
        in_origin ((3,) array): the input volume origin coordinate in the space. Used only if in_bbox is not specified. Default is (0,0,0), meaning the input volume is located at the origin of the underlying space.
        out_bbox ((6,) array): the bounding box that the output volume is defined on. If not given, each dimension is from 0 to the max reach of any structure.
    Returns:
        3d-array: cropped/padded volume
    """
    bounding_box = np.array(bounding_box).astype(np.int)
    xmin, xmax, ymin, ymax, zmin, zmax = bounding_box
    merged_bounding_box = np.array(merged_bounding_box).astype(np.int)
    merged_xmin, merged_xmax, merged_ymin, merged_ymax, merged_zmin, merged_zmax = merged_bounding_box
    merged_xdim = merged_xmax - merged_xmin + 1
    merged_ydim = merged_ymax - merged_ymin + 1
    merged_zdim = merged_zmax - merged_zmin + 1
    if merged_xmin > xmax or merged_xmax < xmin or merged_ymin > ymax or merged_ymax < ymin or merged_zmin > zmax or merged_zmax < zmin:
        return np.zeros((merged_xdim,merged_ydim, merged_zdim), np.int)
    if merged_xmax > xmax:
        volumes = np.pad(volumes, pad_width=[(0,merged_xmax-xmax),(0,0),(0,0)], mode='constant', constant_values=0)
    if merged_ymax > ymax:
        volumes = np.pad(volumes, pad_width=[(0,0),(0,merged_ymax-ymax),(0,0)], mode='constant', constant_values=0)
    if merged_zmax > zmax:
        volumes = np.pad(volumes, pad_width=[(0,0),(0,0),(0, merged_zmax-zmax)], mode='constant', constant_values=0)
    out_vol = np.zeros((merged_xdim , merged_ydim, merged_zdim), volumes.dtype)
    
    out_vol[xmin-merged_xmin:merged_xmax+1-merged_xmin,
            ymin-merged_ymin:merged_ymax+1-merged_ymin,
            zmin-merged_zmin:merged_zmax+1-merged_zmin] = volumes
    assert out_vol.shape[0] == merged_xdim
    assert out_vol.shape[1] == merged_ydim
    assert out_vol.shape[2] == merged_zdim
    return out_vol

def crop_and_pad_volumes(merged_bounding_box=None, bounding_box_volume=None):
    """
    Args:
        out_bbox ((6,)-array): the output bounding box, must use the same reference system as the vol_bbox input.
        vol_bbox 
    Returns:
        list of 3d arrays or dict {structure name: 3d array}
    """
    if isinstance(bounding_box_volume, dict):
        bounding_box_volume = list(bounding_box_volume.items())
    vols = [crop_and_pad_volume(volume, bounding_box, merged_bounding_box=merged_bounding_box) for (volume, bounding_box) in bounding_box_volume]
    # from atlas.BrainStructureManager import Brain
    # brain = Brain('MD585')
    # id = 0
    # axis = 1
    # brain.plotter.plot_3d_image_stack(bounding_box_volume[id][0],axis)
    # brain.plotter.plot_3d_image_stack(vols[id],axis)
    return vols

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

def save_mesh(polydata, filename):
    stlWriter = vtk.vtkSTLWriter()
    stlWriter.SetFileName(filename)
    stlWriter.SetInputData(polydata)
    stlWriter.Write()

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