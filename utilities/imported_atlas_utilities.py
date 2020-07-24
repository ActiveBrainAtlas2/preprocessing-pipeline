import os
import sys
import time
from multiprocessing.pool import Pool
import matplotlib.pyplot as plt

import numpy as np
from pandas import read_hdf
from skimage import io
import json
from collections import defaultdict
import re
from skimage.measure import find_contours, regionprops
from skimage.filters import gaussian

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.sqlcontroller import SqlController
from utilities.alignment_utility import load_hdf, one_liner_to_arr, load_ini, convert_resolution_string_to_um, convert_resolution_string_to_voxel_size
from utilities.file_location import CSHL_DIR as VOLUME_ROOTDIR, FileLocationManager
from utilities.coordinates_converter import CoordinatesConverter
SECTION_THICKNESS = 20. # in um
REGISTRATION_PARAMETERS_ROOTDIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_registration_parameters'


# print all_structures_total


def create_alignment_specs(stack, detector_id):
    fn_global = stack + '_visualization_global_alignment_spec.json'
    data = {}

    data["stack_m"] = {
        "name": "atlasV7",
        "vol_type": "score",
        "resolution": "10.0um"
    }
    data["stack_f"] = {
        "name": stack,
        "vol_type": "score",
        "resolution": "10.0um",
        "detector_id": detector_id
    }
    data["warp_setting"] = 0

    with open(fn_global, 'w') as outfile:
        json.dump(data, outfile)

    data = {}
    json_structure_list = []
    for structure in all_structures_total:
        data[structure] = {
            "stack_m":
                {
                    "name": "atlasV7",
                    "vol_type": "score",
                    "structure": [structure],
                    "resolution": "10.0um"
                },
            "stack_f":
                {
                    "name": stack,
                    "vol_type": "score",
                    "structure": [structure],
                    "resolution": "10.0um",
                    "detector_id": detector_id
                },
            "warp_setting": 7
        }

    fn_structure = stack + '_visualization_per_structure_alignment_spec.json'

    with open(fn_structure, 'w') as outfile:
        json.dump(data, outfile)

    return fn_global, fn_structure


# Load volumes, convert to proper coordinates, export as contours
def get_structure_contours_from_structure_volumes_v3(volumes, stack, sections,
                                                     resolution, level, sample_every=1,
                                                     use_unsided_name_as_key=False):
    """
    Re-section atlas volumes and obtain structure contours on each section.
    Resolution of output contours are in volume resolution.
    v3 supports multiple levels.

    Args:
        volumes (dict of (3D array, 3-tuple)): {structure: (volume, origin_wrt_wholebrain)}. volume is a 3d array of probability values.
        sections (list of int):
        resolution (int): resolution of input volumes.
        level (float or dict or dict of list): the cut-off probability at which surfaces are generated from probabilistic volumes. Default is 0.5.
        sample_every (int): how sparse to sample contour vertices.

    Returns:
        Dict {section: {name_s: contour vertices}}.
    """
    sqlController = SqlController(stack)

    structure_contours_wrt_alignedBrainstemCrop_rawResol = defaultdict(lambda: defaultdict(dict))
    section_numbers = sqlController.get_sections_numbers(stack)
    converter = CoordinatesConverter(stack=stack, section_list=section_numbers)
    # converter = CoordinatesConverter(stack=stack, section_list=metadata_cache['sections_to_filenames'][stack].keys())

    converter.register_new_resolution('structure_volume', resol_um=convert_resolution_string_to_um(stack, resolution))
    converter.register_new_resolution('image', resol_um=convert_resolution_string_to_um(stack, 'raw'))

    for name_s, (structure_volume_volResol, origin_wrt_wholebrain_volResol) in volumes.items():
        print(name_s, (structure_volume_volResol, origin_wrt_wholebrain_volResol))
        converter.derive_three_view_frames(name_s,
                                           origin_wrt_wholebrain_um=convert_resolution_string_to_um(stack,
                                                                                                    resolution) * origin_wrt_wholebrain_volResol,
                                           zdim_um=convert_resolution_string_to_um(stack, resolution) *
                                                   structure_volume_volResol.shape[2])
        positions_of_all_sections_wrt_structureVolume = converter.convert_frame_and_resolution(
            p=np.array(sections)[:, None],
            in_wrt=('wholebrain', 'sagittal'), in_resolution='section',
            out_wrt=(name_s, 'sagittal'), out_resolution='structure_volume', stack=stack)[..., 2].flatten()

        structure_ddim = structure_volume_volResol.shape[2]
        print('structure_ddim', structure_ddim)
        print('sections', sections)
        #print('type sections', type(sections))
        #positions_of_all_sections_wrt_structureVolume = np.arange(49, 176)
        print('positions_of_all_sections_wrt_structureVolume', positions_of_all_sections_wrt_structureVolume)
        print('type positions_of_all_sections_wrt_structureVolume', type(positions_of_all_sections_wrt_structureVolume))
        ###TODO fix, positions_of_all_sections_wrt_structureVolume < structure_ddim
        valid_mask = (positions_of_all_sections_wrt_structureVolume >= 0) & (
                    positions_of_all_sections_wrt_structureVolume < structure_ddim)
        #valid_mask = (positions_of_all_sections_wrt_structureVolume >= 400) & (
        #            positions_of_all_sections_wrt_structureVolume < 500)
        if np.count_nonzero(valid_mask) == 0:
            print('valid_mask is empty')
            continue

        positions_of_all_sections_wrt_structureVolume = positions_of_all_sections_wrt_structureVolume[valid_mask]
        positions_of_all_sections_wrt_structureVolume = np.round(positions_of_all_sections_wrt_structureVolume).astype(
            np.int)

        if isinstance(level, dict):
            level_this_structure = level[name_s]
        else:
            level_this_structure = level

        if isinstance(level_this_structure, float):
            level_this_structure = [level_this_structure]

        for one_level in level_this_structure:

            contour_2d_wrt_structureVolume_sectionPositions_volResol = \
                find_contour_points_3d(structure_volume_volResol >= one_level,
                                       along_direction='sagittal',
                                       sample_every=sample_every,
                                       positions=positions_of_all_sections_wrt_structureVolume)

            for d_wrt_structureVolume, cnt_uv_wrt_structureVolume in contour_2d_wrt_structureVolume_sectionPositions_volResol.items():

                contour_3d_wrt_structureVolume_volResol = np.column_stack(
                    [cnt_uv_wrt_structureVolume, np.ones((len(cnt_uv_wrt_structureVolume),)) * d_wrt_structureVolume])

                #             contour_3d_wrt_wholebrain_uv_rawResol_section = converter.convert_frame_and_resolution(
                #                 p=contour_3d_wrt_structureVolume_volResol,
                #                 in_wrt=(name_s, 'sagittal'), in_resolution='structure_volume',
                #                 out_wrt=('wholebrain', 'sagittal'), out_resolution='image_image_section')

                contour_3d_wrt_alignedBrainstemCrop_uv_rawResol_section = converter.convert_frame_and_resolution(
                    p=contour_3d_wrt_structureVolume_volResol,
                    in_wrt=(name_s, 'sagittal'), in_resolution='structure_volume',
                    out_wrt=('wholebrainXYcropped', 'sagittal'), out_resolution='image_image_section', stack=stack)

                assert len(np.unique(contour_3d_wrt_alignedBrainstemCrop_uv_rawResol_section[:, 2])) == 1
                sec = int(contour_3d_wrt_alignedBrainstemCrop_uv_rawResol_section[0, 2])

                if use_unsided_name_as_key:
                    name = convert_to_unsided_label(name_s)
                else:
                    name = name_s

                structure_contours_wrt_alignedBrainstemCrop_rawResol[sec][name][
                    one_level] = contour_3d_wrt_alignedBrainstemCrop_uv_rawResol_section[..., :2]

    return structure_contours_wrt_alignedBrainstemCrop_rawResol


def find_contour_points_3d(labeled_volume, along_direction, positions=None, sample_every=10):
    """
    Find the cross-section contours given a (binary?) volume.
    Args:
        labeled_volume (3D ndarray of int): integer-labeled volume.
        along_direction (str): x/coronal, y/horizontal or z/sagittal.
        positions (None or list of int): if None, find contours at all positions of input volume, from 0 to the depth of volume.
    Returns:
        dict {int: (n,2)-ndarray}: contours. {voxel position: contour vertices (second dim, first dim)}.
        For example, If `along_direction=y`, returns (z,x); if direction=x, returns (z,y).
    """

    import multiprocessing
    # nproc = multiprocessing.cpu_count()
    nproc = 1

    if along_direction == 'z' or along_direction == 'sagittal':
        if positions is None:
            positions = range(0, labeled_volume.shape[2])
    elif along_direction == 'x' or along_direction == 'coronal':
        if positions is None:
            positions = range(0, labeled_volume.shape[1])
    elif along_direction == 'y' or along_direction == 'horizontal':
        if positions is None:
            positions = range(0, labeled_volume.shape[0])

    def find_contour_points_slice(p):
        """
        Args:
            p (int): position
        """
        print('p', p, 'labeled_volume.shape', labeled_volume.shape)
        if along_direction == 'x':
            if p < 0 or p >= labeled_volume.shape[1]:
                return
            vol_slice = labeled_volume[:, p, :]
        elif along_direction == 'coronal':
            if p < 0 or p >= labeled_volume.shape[1]:
                return
            vol_slice = labeled_volume[:, p, ::-1]
        elif along_direction == 'y':
            if p < 0 or p >= labeled_volume.shape[0]:
                return
            vol_slice = labeled_volume[p, :, :]
        elif along_direction == 'horizontal':
            if p < 0 or p >= labeled_volume.shape[0]:
                return
            vol_slice = labeled_volume[p, :, ::-1].T
        elif along_direction == 'z' or along_direction == 'sagittal':
            if p < 0 or p >= labeled_volume.shape[2]:
                return
            vol_slice = labeled_volume[:, :, p]
        else:
            raise
        print('vol_slice', vol_slice)
        cnts = find_contour_points(vol_slice.astype(np.uint8), sample_every=sample_every)
        if len(cnts) == 0 or 1 not in cnts:
            # sys.stderr.write('No contour of reconstructed volume is found at position %d.\n' % p)
            return
        else:
            if len(cnts[1]) > 1:
                sys.stderr.write(
                    '%s contours of reconstructed volume is found at position %d (%s). Use the longest one.\n' % (
                    len(cnts[1]), p, map(len, cnts[1])))
                cnt = np.array(cnts[1][np.argmax(map(len, cnts[1]))])
            else:
                cnt = np.array(cnts[1][0])
            if len(cnt) <= 2:
                sys.stderr.write('contour has less than three vertices. Ignore.\n')
                return
            else:
                return cnt

    #####TODO fix this, hard coding values just to get a response
    #pool = Pool(nproc)
    print('positions', positions)
    #positions = [60,70,75,77,78,80,86,200]
    contours = dict()
    #pm = pool.map(find_contour_points_slice, positions)
    for p in positions:
        r = find_contour_points_slice(p)
        contours[p] = r
    #print(pm)
    #contours = dict(zip(positions, pool.map(find_contour_points_slice, positions)))
    #pool.close()
    #pool.join()

    contours = {p: cnt for p, cnt in contours.items() if cnt is not None}
    print('contours', contours)
    return contours


def find_contour_points(labelmap, sample_every=10, min_length=0):
    """
    Find contour coordinates.
    Args:
        labelmap (2d array of int): integer-labeled 2D image
        sample_every (int): can be interpreted as distance between points.
        min_length (int): contours with fewer vertices are discarded.
        This argument is being deprecated because the vertex number does not
        reliably measure actual contour length in microns.
        It is better to leave this decision to calling routines.
    Returns:
        a dict of lists: {label: list of contours each consisting of a list of (x,y) coordinates}
    """

    padding = 5

    if np.count_nonzero(labelmap) == 0:
        # sys.stderr.write('No contour can be found because the image is blank.\n')
        return {}

    regions = regionprops(labelmap.astype(np.int))
    contour_points = {}

    for r in regions:

        (min_row, min_col, max_row, max_col) = r.bbox

        padded = np.pad(r.filled_image, ((padding, padding), (padding, padding)),
                        mode='constant', constant_values=0)

        contours = find_contours(padded, level=.5, fully_connected='high')
        contours = [cnt.astype(np.int) for cnt in contours if len(cnt) > min_length]
        if len(contours) > 0:
            #             if len(contours) > 1:
            #                 sys.stderr.write('%d: region has more than one part\n' % r.label)

            contours = sorted(contours, key=lambda c: len(c), reverse=True)
            contours_list = [c - (padding, padding) for c in contours]
            contour_points[r.label] = sorted([c[np.arange(0, c.shape[0], sample_every)][:, ::-1] + (min_col, min_row)
                                              for c in contours_list], key=lambda c: len(c), reverse=True)

        elif len(contours) == 0:
            #             sys.stderr.write('no contour is found\n')
            continue

    #         viz = np.zeros_like(r.filled_image)
    #         viz[pts_sampled[:,0], pts_sampled[:,1]] = 1
    #         plt.imshow(viz, cmap=plt.cm.gray);
    #         plt.show();

    return contour_points


def convert_to_unsided_label(label):
    structure_name, side, surround_margin, surround_structure_name = parse_label(label)
    return compose_label(structure_name, side=None, surround_margin=surround_margin,
                         surround_structure_name=surround_structure_name)


def compose_label(structure_name, side=None, surround_margin=None, surround_structure_name=None, singular_as_s=False):
    label = structure_name
    if side is not None:
        if not singular_as_s and side == 'S':
            pass
        else:
            label += '_' + side
    if surround_margin is not None:
        label += '_surround_' + surround_margin
    if surround_structure_name is not None:
        label += '_' + surround_structure_name
    return label


def parse_label(label, singular_as_s=False):
    """
    Args:
        singular_as_s (bool): If true, singular structures have side = 'S', otherwise side = None.

    Returns:
        (structure name, side, surround margin, surround structure name)
    """
    try:
        m = re.match("([0-9a-zA-Z]*)(_(L|R))?(_surround_(.+)_([0-9a-zA-Z]*))?", label)
    except:
        raise Exception("Parse label error: %s" % label)
    g = m.groups()
    structure_name = g[0]
    side = g[2]
    if side is None:
        if singular_as_s:
            side = 'S'
    surround_margin = g[4]
    surround_structure_name = g[5]

    return structure_name, side, surround_margin, surround_structure_name


def load_hdf_v2(fn, key='data'):
    import pandas
    return pandas.read_hdf(fn, key)


def load_sorted_filenames(stack):
    sorted_filenames_path = os.path.join(os.environ['ATLAS_DATA_ROOT_DIR'], 'CSHL_data_processed', stack,
                                         stack + '_sorted_filenames.txt')

    with open(sorted_filenames_path, 'r') as sf:
        sorted_filenames_string = sf.read()
    sorted_filenames_list = sorted_filenames_string.split('\n')[0:len(sorted_filenames_string.split('\n')) - 1]

    sorted_filenames = [{}, {}]  # filename_to_section, section_to_filename

    for sorted_fn_line in sorted_filenames_list:
        filename, slice_num = sorted_fn_line.split(' ')
        slice_num = int(slice_num)
        if filename == 'Placeholder':
            continue

        sorted_filenames[0][filename] = slice_num
        sorted_filenames[1][slice_num] = filename

    return sorted_filenames


def get_image_filepath_v2(stack, prep_id, resol, version, fn):
    image_filepath_root = os.path.join(os.environ['ATLAS_DATA_ROOT_DIR'], 'CSHL_data_processed', stack, \
                                       stack + '_prep' + str(prep_id) + '_' + resol + '_' + version)

    return os.path.join(image_filepath_root, fn + '_prep' + str(prep_id) + '_' + resol + '_' + version + '.tif')


def load_json(fp):
    with open(fp, 'r') as json_file:
        return json.load(json_file)


def get_transformed_volume_filepath_v2(alignment_spec, resolution=None, trial_idx=None, structure=None):
    if resolution is None:
        if 'resolution' in alignment_spec['stack_m']:
            resolution = alignment_spec['stack_m']['resolution']

    if structure is None:
        if 'structure' in alignment_spec['stack_m']:
            structure = alignment_spec['stack_m']['structure']

    warp_basename = get_warped_volume_basename_v2(alignment_spec=alignment_spec,
                                                  trial_idx=trial_idx)
    vol_basename = warp_basename + '_' + resolution
    vol_basename_with_structure_suffix = vol_basename + ('_' + structure) if structure is not None else ''
    # print('1',VOLUME_ROOTDIR)
    # print('2',alignment_spec['stack_m']['name'])
    # print('3',vol_basename)
    # print('4 score_volumes')
    # print('5',vol_basename_with_structure_suffix)
    # print('get transformed_volume_filepath ', filename)
    filename = os.path.join('/home/eddyod/MouseBrainSlicer_data/score_volumes', 'atlasV7_10.0um_scoreVolume_12N.npy')
    return filename


def get_warped_volume_basename_v2(alignment_spec, trial_idx=None):
    """
    Args:
        alignment_spec (dict): must have these keys warp_setting, stack_m and stack_f
    """

    warp_setting = alignment_spec['warp_setting']
    basename_m = get_original_volume_basename_v2(alignment_spec['stack_m'])
    basename_f = get_original_volume_basename_v2(alignment_spec['stack_f'])
    vol_name = basename_m + '_warp%(warp)d_' % {'warp': warp_setting} + basename_f

    if trial_idx is not None:
        vol_name += '_trial_%d' % trial_idx

    return vol_name


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


def volume_type_to_str(t):
    if t == 'score':
        return 'scoreVolume'
    elif t == 'annotation':
        return 'annotationVolume'
    elif t == 'annotationAsScore':
        return 'annotationAsScoreVolume'
    elif t == 'annotationSmoothedAsScore':
        return 'annotationSmoothedAsScoreVolume'
    elif t == 'outer_contour':
        return 'outerContourVolume'
    elif t == 'intensity':
        return 'intensityVolume'
    elif t == 'intensity_metaimage':
        return 'intensityMetaImageVolume'
    else:
        raise Exception('Volume type %s is not recognized.' % t)


def load_data(filepath, filetype=None):
    if not os.path.exists(filepath):
        sys.stderr.write('load_data: File does not exist: %s\n' % filepath)

    if filetype == 'bp':
        import bloscpack as bp
        return bp.unpack_ndarray_from_file(filepath)
    elif filetype == 'npy':
        return np.load(filepath)
    elif filetype == 'image':
        return io.imread(filepath)
    elif filetype == 'hdf':
        try:
            return load_hdf(filepath)
        except:
            return load_hdf_v2(filepath)
    elif filetype == 'bbox':
        return np.loadtxt(filepath).astype(np.int)
    elif filetype == 'annotation_hdf':
        contour_df = read_hdf(filepath, 'contours')
        return contour_df
    elif filetype == 'pickle':
        import cPickle as pickle
        return pickle.load(open(filepath, 'r'))
    elif filetype == 'file_section_map':
        with open(filepath, 'r') as f:
            fn_idx_tuples = [line.strip().split() for line in f.readlines()]
            filename_to_section = {fn: int(idx) for fn, idx in fn_idx_tuples}
            section_to_filename = {int(idx): fn for fn, idx in fn_idx_tuples}
        return filename_to_section, section_to_filename
    elif filetype == 'label_name_map':
        label_to_name = {}
        name_to_label = {}
        with open(filepath, 'r') as f:
            for line in f.readlines():
                name_s, label = line.split()
                label_to_name[int(label)] = name_s
                name_to_label[name_s] = int(label)
        return label_to_name, name_to_label
    elif filetype == 'anchor':
        with open(filepath, 'r') as f:
            anchor_fn = f.readline().strip()
        return anchor_fn
    elif filetype == 'transform_params':
        with open(filepath, 'r') as f:
            lines = f.readlines()

            global_params = one_liner_to_arr(lines[0], float)
            centroid_m = one_liner_to_arr(lines[1], float)
            xdim_m, ydim_m, zdim_m = one_liner_to_arr(lines[2], int)
            centroid_f = one_liner_to_arr(lines[3], float)
            xdim_f, ydim_f, zdim_f = one_liner_to_arr(lines[4], int)

        return global_params, centroid_m, centroid_f, xdim_m, ydim_m, zdim_m, xdim_f, ydim_f, zdim_f
    else:
        sys.stderr.write('File type %s not recognized.\n' % filetype)


def load_transformed_volume(alignment_spec, structure):
    """
    Args:
        alignment_spec (dict): specify stack_m, stack_f, warp_setting.
        resolution (str): resolution of the output volume.
        legacy (bool): if legacy, resolution can only be down32.

    Returns:
        (2-tuple): (volume, bounding box wrt "wholebrain" domain of the fixed stack)

    """
    kwargs = locals()

    volume_filename = get_transformed_volume_filepath_v2(alignment_spec=alignment_spec,
                                                         resolution=None,
                                                         structure=structure)
    origin_filename = get_transformed_volume_origin_filepath(wrt='fixedWholebrain',
                                                             alignment_spec=alignment_spec,
                                                             resolution=None,
                                                             structure=structure)
    print('load_transformed_volume: volume_filename', volume_filename)
    print('load_transformed_volume: origin_filename', origin_filename)
    origin_filename = '/home/eddyod/MouseBrainSlicer_data/score_volumes/atlasV7_10.0um_scoreVolume_12N_origin_wrt_canonicalAtlasSpace.txt'
    volume = load_data(volume_filename)
    origin = load_data(origin_filename)
    return (volume, origin)


def get_transformed_volume_origin_filepath(alignment_spec, structure=None, wrt='wholebrain', resolution=None):
    """
    Args:
        alignment_spec (dict): specifies the multi-map.
        wrt (str): specify which domain is the bounding box relative to.
        resolution (str): specifies the resolution of the multi-map.
        structure (str): specifies one map of the multi-map.
    """

    if resolution is None:
        if 'resolution' in alignment_spec['stack_m']:
            resolution = alignment_spec['stack_m']['resolution']

    if structure is None:
        if 'structure' in alignment_spec['stack_m']:
            structure = alignment_spec['stack_m']['structure']

    warp_basename = get_warped_volume_basename_v2(alignment_spec=alignment_spec, trial_idx=None)
    vol_basename = warp_basename + '_' + resolution
    vol_basename_with_structure_suffix = vol_basename + ('_' + structure if structure is not None else '')

    return os.path.join(VOLUME_ROOTDIR, alignment_spec['stack_m']['name'],
                        vol_basename, 'score_volumes',
                        vol_basename_with_structure_suffix + '_origin_wrt_' + wrt + '.txt')


def get_cropbox_filename_v2(stack, anchor_fn=None, prep_id=2):
    """
    Return path to file that specified the cropping box of the given crop specifier.

    Args:
        prep_id (int or str): 2D frame specifier
    """

    fp = os.path.join(get_images_root_folder(stack), stack + '_cropbox.ini')
    return fp


def get_images_root_folder(stack):
    fileLocationManager = FileLocationManager(stack)
    # return os.path.join( os.environ['ROOT_DIR'], stack, 'preprocessing_data' )
    return fileLocationManager.tif


## stack=stack, prep_id='alignedBrainstemCrop', only_2d=True
def load_cropbox_v2(stack, anchor_fn=None, convert_section_to_z=False, prep_id=2,
                    return_origin_instead_of_bbox=False,
                    return_dict=False, only_2d=True):
    """
    Loads the cropping box for the given crop at thumbnail (downsample 32 times from raw) resolution.

    Args:
        convert_section_to_z (bool): If true, return (xmin,xmax,ymin,ymax,zmin,zmax) where z=0 is section #1; if false, return (xmin,xmax,ymin,ymax,secmin,secmax)
        prep_id (int)
    """

    xmin = 520
    xmax = 1004
    ymin = 128
    ymax = 496

    cropbox = np.array((xmin, xmax, ymin, ymax))
    return cropbox.astype(np.int)


def load_original_volume_v2(stack_spec, structure=None, resolution=None, bbox_wrt='wholebrain',
                            return_origin_instead_of_bbox=True,
                            crop_to_minimal=False):
    """
    Args:

    Returns:
        (3d-array, (6,)-tuple): (volume, bounding box wrt wholebrain)
    """

    # volume_filename = get_original_volume_filepath_v2(stack_spec=stack_spec, structure=structure, resolution=resolution)
    # download_from_s3(vol_fp, is_dir=False)
    volume_filename = '/net/birdstore/Active_Atlas_Data/copied_from_S3/mousebrainatlas-data/CSHL_volumes/MD589/MD589_wholebrainWithMargin_10.0um_intensityVolume/MD589_wholebrainWithMargin_10.0um_intensityVolume.bp'
    # print('volume_filename', volume_filename)
    volume = load_data(volume_filename, filetype='bp')

    # bbox_fp = DataManager.get_original_volume_bbox_filepath_v2(stack_spec=stack_spec, structure=structure,
    #                                                            resolution=resolution, wrt=bbox_wrt)
    # download_from_s3(bbox_fp)
    # volume_bbox = DataManager.load_data(bbox_fp, filetype='bbox')

    # origin_filename = get_original_volume_origin_filepath_v3(stack_spec=stack_spec, structure=structure, wrt=bbox_wrt, resolution=resolution)
    # print('origin_file_name', origin_filename)
    origin_filename = '/net/birdstore/Active_Atlas_Data/copied_from_S3/mousebrainatlas-data/CSHL_volumes/MD589/MD589_wholebrainWithMargin_10.0um_intensityVolume/MD589_wholebrainWithMargin_10.0um_intensityVolume_origin_wrt_wholebrain.txt'
    # origin = load_data(origin_filename)
    origin = np.array([1.470000000000000000e+02, 9.800000000000000000e+01, 1.820000000000000000e+02])

    if crop_to_minimal:
        volume, origin = crop_volume_to_minimal(vol=volume, origin=origin, return_origin_instead_of_bbox=True)

    # if return_origin_instead_of_bbox:
    return volume, origin
    # else:
    #     convert_frame
    #     return volume, volume_bbox


def crop_volume_to_minimal(vol, origin=(0, 0, 0), margin=0, return_origin_instead_of_bbox=True):
    """
    Returns:
        (nonzero part of volume, origin of cropped volume)
    """
    xmin, xmax, ymin, ymax, zmin, zmax = bbox_3d(vol)
    xmin = max(0, xmin - margin)
    ymin = max(0, ymin - margin)
    zmin = max(0, zmin - margin)
    xmax = min(vol.shape[1] - 1, xmax + margin)
    ymax = min(vol.shape[0] - 1, ymax + margin)
    zmax = min(vol.shape[2] - 1, zmax + margin)

    if return_origin_instead_of_bbox:
        return vol[ymin:ymax + 1, xmin:xmax + 1, zmin:zmax + 1], np.array(origin) + (xmin, ymin, zmin)
    else:
        return vol[ymin:ymax + 1, xmin:xmax + 1, zmin:zmax + 1], np.array(origin)[[0, 0, 1, 1, 2, 2]] + (
        xmin, xmax, ymin, ymax, zmin, zmax)


def bbox_3d(img):
    r = np.any(img, axis=(1, 2))
    c = np.any(img, axis=(0, 2))
    z = np.any(img, axis=(0, 1))

    try:
        rmin, rmax = np.where(r)[0][[0, -1]]
        cmin, cmax = np.where(c)[0][[0, -1]]
        zmin, zmax = np.where(z)[0][[0, -1]]
    except:
        raise Exception('Input is empty.\n')

    return cmin, cmax, rmin, rmax, zmin, zmax


def get_original_volume_origin_filepath_v3(stack_spec, structure, wrt='wholebrain', resolution=None):
    fileLocationManager = FileLocationManager(stack_spec['name'])
    volume_type = stack_spec['vol_type']

    if 'resolution' not in stack_spec or stack_spec['resolution'] is None:
        assert resolution is not None
        stack_spec['resolution'] = resolution

    if 'structure' not in stack_spec or stack_spec['structure'] is None:
        vol_basename = get_original_volume_basename_v2(stack_spec=stack_spec)
    else:
        stack_spec_no_structure = stack_spec.copy()
        stack_spec_no_structure['structure'] = None
        vol_basename = get_original_volume_basename_v2(stack_spec=stack_spec_no_structure)

    if volume_type == 'score' or volume_type == 'annotationAsScore':
        origin_fp = os.path.join(VOLUME_ROOTDIR, '%(stack)s',
                                 '%(basename)s',
                                 'score_volumes',
                                 '%(basename)s_%(struct)s_origin' + (
                                     '_wrt_' + wrt if wrt is not None else '') + '.txt') % \
                    {'stack': stack_spec['name'], 'basename': vol_basename, 'struct': structure}

    elif volume_type == 'intensity':
        origin_fp = os.path.join(fileLocationManager.atlas_volume, vol_basename,
                                 vol_basename + '_origin' + ('_wrt_' + wrt if wrt is not None else '') + '.txt')
    else:
        raise Exception("vol_type of %s is not recognized." % stack_spec['vol_type'])

    return origin_fp


def get_original_volume_filepath_v2(stack_spec, structure=None, resolution=None):
    """
    Args:
        stack_spec (dict): keys are:
                            - name
                            - resolution
                            - prep_id (optional)
                            - detector_id (optional)
                            - structure (optional)
                            - vol_type
    """
    fileLocationManager = FileLocationManager(stack_spec['name'])

    if 'resolution' not in stack_spec or stack_spec['resolution'] is None:
        assert resolution is not None
        stack_spec['resolution'] = resolution

    if 'structure' not in stack_spec or stack_spec['structure'] is None:
        vol_basename = get_original_volume_basename_v2(stack_spec=stack_spec)
    else:
        stack_spec_no_structure = stack_spec.copy()
        stack_spec_no_structure['structure'] = None
        vol_basename = get_original_volume_basename_v2(stack_spec=stack_spec_no_structure)

    vol_basename_with_structure_suffix = vol_basename + ('_' + structure) if structure is not None else ''

    if stack_spec['vol_type'] == 'score':
        return os.path.join(fileLocationManager.atlas_volume, vol_basename_with_structure_suffix + '.npy')
    elif stack_spec['vol_type'] == 'annotationAsScore':
        return os.path.join(fileLocationManager.atlas_volume, vol_basename_with_structure_suffix + '.npy')
    elif stack_spec['vol_type'] == 'intensity':
        return os.path.join(fileLocationManager.atlas_volume, vol_basename, vol_basename + '.npy')
    else:
        raise Exception("vol_type of %s is not recognized." % stack_spec['vol_type'])


##### stuff imported for building the atlas

def get_overall_bbox(vol_bbox_tuples=None, bboxes=None):
    vol_bbox_tuples = list(vol_bbox_tuples)
    if bboxes is None:
        bboxes = np.array([b for v, b in vol_bbox_tuples])
    xmin, ymin, zmin = np.min(bboxes[:, [0,2,4]], axis=0)
    xmax, ymax, zmax = np.max(bboxes[:, [1,3,5]], axis=0)
    bbox = xmin, xmax, ymin, ymax, zmin, zmax
    return bbox


def crop_and_pad_volume(in_vol, in_bbox=None, in_origin=(0,0,0), out_bbox=None):
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

    if in_bbox is None:
        assert in_origin is not None
        in_xmin, in_ymin, in_zmin = in_origin
        in_xmax = in_xmin + in_vol.shape[1] - 1
        in_ymax = in_ymin + in_vol.shape[0] - 1
        in_zmax = in_zmin + in_vol.shape[2] - 1
    else:
        in_bbox = np.array(in_bbox).astype(np.int)
        in_xmin, in_xmax, in_ymin, in_ymax, in_zmin, in_zmax = in_bbox
    #FIXME what is this code doing below?
    in_xdim = in_xmax - in_xmin + 1
    in_ydim = in_ymax - in_ymin + 1
    in_zdim = in_zmax - in_zmin + 1
        # print 'in', in_xdim, in_ydim, in_zdim

    if out_bbox is None:
        out_xmin = 0
        out_ymin = 0
        out_zmin = 0
        out_xmax = in_xmax
        out_ymax = in_ymax
        out_zmax = in_zmax
    elif isinstance(out_bbox, np.ndarray) and out_bbox.ndim == 3:
        out_xmin, out_xmax, out_ymin, out_ymax, out_zmin, out_zmax = (0, out_bbox.shape[1]-1, 0, out_bbox.shape[0]-1, 0, out_bbox.shape[2]-1)
    else:
        out_bbox = np.array(out_bbox).astype(np.int)
        out_xmin, out_xmax, out_ymin, out_ymax, out_zmin, out_zmax = out_bbox
    out_xdim = out_xmax - out_xmin + 1
    out_ydim = out_ymax - out_ymin + 1
    out_zdim = out_zmax - out_zmin + 1

    # print out_xmin, out_xmax, out_ymin, out_ymax, out_zmin, out_zmax

    if out_xmin > in_xmax or out_xmax < in_xmin or out_ymin > in_ymax or out_ymax < in_ymin or out_zmin > in_zmax or out_zmax < in_zmin:
        return np.zeros((out_ydim, out_xdim, out_zdim), np.int)

    if out_xmax > in_xmax:
        in_vol = np.pad(in_vol, pad_width=[(0,0),(0, out_xmax-in_xmax),(0,0)], mode='constant', constant_values=0)
        # print 'pad x'
    if out_ymax > in_ymax:
        in_vol = np.pad(in_vol, pad_width=[(0, out_ymax-in_ymax),(0,0),(0,0)], mode='constant', constant_values=0)
        # print 'pad y'
    if out_zmax > in_zmax:
        in_vol = np.pad(in_vol, pad_width=[(0,0),(0,0),(0, out_zmax-in_zmax)], mode='constant', constant_values=0)
        # print 'pad z'

    out_vol = np.zeros((out_ydim, out_xdim, out_zdim), in_vol.dtype)
    ymin = max(in_ymin, out_ymin)
    xmin = max(in_xmin, out_xmin)
    zmin = max(in_zmin, out_zmin)
    ymax = out_ymax
    xmax = out_xmax
    zmax = out_zmax
    # print 'in_vol', np.array(in_vol.shape)[[1,0,2]]
    # print xmin, xmax, ymin, ymax, zmin, zmax
    # print xmin-in_xmin, xmax+1-in_xmin
    # assert ymin >= 0 and xmin >= 0 and zmin >= 0
    out_vol[ymin-out_ymin:ymax+1-out_ymin,
            xmin-out_xmin:xmax+1-out_xmin,
            zmin-out_zmin:zmax+1-out_zmin] = in_vol[ymin-in_ymin:ymax+1-in_ymin, xmin-in_xmin:xmax+1-in_xmin, zmin-in_zmin:zmax+1-in_zmin]

    assert out_vol.shape[1] == out_xdim
    assert out_vol.shape[0] == out_ydim
    assert out_vol.shape[2] == out_zdim

    return out_vol

def crop_and_pad_volumes(out_bbox=None, vol_bbox_dict=None, vol_bbox_tuples=None, vol_bbox=None):
    """
    Args:
        out_bbox ((6,)-array): the output bounding box, must use the same reference system as the vol_bbox input.
        vol_bbox_dict (dict {key: (vol, bbox)})
        vol_bbox_tuples (list of (vol, bbox) tuples)
    Returns:
        list of 3d arrays or dict {structure name: 3d array}
    """

    if vol_bbox is not None:
        if isinstance(vol_bbox, dict):
            vols = {l: crop_and_pad_volume(v, in_bbox=b, out_bbox=out_bbox) for l, (v, b) in volumes.items()}
        elif isinstance(vol_bbox, list):
            vols = [crop_and_pad_volume(v, in_bbox=b, out_bbox=out_bbox) for (v, b) in volumes]
        else:
            raise
    else:
        if vol_bbox_tuples is not None:
            vols = [crop_and_pad_volume(v, in_bbox=b, out_bbox=out_bbox) for (v, b) in vol_bbox_tuples]
        elif vol_bbox_dict is not None:
            vols = {l: crop_and_pad_volume(v, in_bbox=b, out_bbox=out_bbox) for l, (v, b) in vol_bbox_dict.items()}
        else:
            raise

    return vols

def convert_vol_bbox_dict_to_overall_vol(vol_bbox_dict=None, vol_bbox_tuples=None, vol_origin_dict=None):
    """
    Must provide exactly one of the three choices of arguments.
    `bbox` or `origin` can be provided as float, but will be casted as integer before cropping and padding.
    Args:
        vol_bbox_dict (dict {key: 3d-array of float32, 6-tuple of float}): represents {name_s: (vol, bbox)}
        vol_origin_dict (dict {key: 3d-array of float32, 3-tuple of float}): represents {name_s: (vol, origin)}
    Returns:
        (list or dict of 3d arrays, (6,)-ndarray of int): (volumes in overall coordinate system, the common overall bounding box)
    """

    if vol_origin_dict is not None:
        vol_bbox_dict = {k: (v, (o[0], o[0]+v.shape[1]-1, o[1], o[1]+v.shape[0]-1, o[2], o[2]+v.shape[2]-1)) for k,(v,o) in vol_origin_dict.items()}

    if vol_bbox_dict is not None:
        volume_bbox = np.round(get_overall_bbox(vol_bbox_tuples=vol_bbox_dict.values())).astype(np.int)
        volumes = crop_and_pad_volumes(out_bbox=volume_bbox, vol_bbox_dict=vol_bbox_dict)
    else:
        volume_bbox = np.round(get_overall_bbox(vol_bbox_tuples=vol_bbox_tuples)).astype(np.int)
        volumes = crop_and_pad_volumes(out_bbox=volume_bbox, vol_bbox_tuples=vol_bbox_tuples)
    return volumes, np.array(volume_bbox)

def load_original_volume_all_known_structures_v3(stack_spec, structures):

    in_bbox_wrt = 'wholebrain'
    return_label_mappings = False
    name_or_index_as_key = 'name'
    common_shape = False
    return_origin_instead_of_bbox = True
    """
    Load original (un-transformed) volumes for all structures and optionally pad them into a common shape.

    Args:
        common_shape (bool): If true, volumes are padded to the same shape.
        in_bbox_wrt (str): the bbox origin for the bbox files currently stored.
        loaded_cropbox_resolution (str): resolution in which the loaded cropbox is defined on.

    Returns:
        If `common_shape` is True:
            if return_label_mappings is True, returns (volumes, common_bbox, structure_to_label, label_to_structure), volumes is dict.
            else, returns (volumes, common_bbox).
        Note that `common_bbox` is relative to the same origin the individual volumes' bounding boxes are (which, ideally, one can infer from the bbox filenames (TODO: systematic renaming)).
        If `common_shape` is False:
            if return_label_mappings is True, returns (dict of volume_bbox_tuples, structure_to_label, label_to_structure).
            else, returns volume_bbox_tuples.
    """

    loaded = False
    sys.stderr.write('Prior structure/index map not found. Generating a new one.\n')

    volumes = {}

    if not loaded:
        structure_to_label = {}
        label_to_structure = {}
        index = 1

    for structure in structures:
        try:
            if loaded:
                index = structure_to_label[structure]

            v, o = load_original_volume_v2(stack_spec, structure=structure,
                                                       bbox_wrt=in_bbox_wrt,
                                                       resolution=stack_spec['resolution'])

            in_bbox_origin_wrt_wholebrain = get_domain_origin(stack=stack_spec['name'],
                                                                          domain=in_bbox_wrt,
                                                                          resolution=stack_spec['resolution'],
                                                                          loaded_cropbox_resolution=stack_spec['resolution'])
            o = o + in_bbox_origin_wrt_wholebrain
            #print('structure', structure, 'v',v,'o',o)
            if name_or_index_as_key == 'name':
                volumes[structure] = (v,o)
            else:
                volumes[index] = (v,o)

            if not loaded:
                structure_to_label[structure] = index
                label_to_structure[index] = structure
                index += 1

        except Exception as e:
            raise e
            sys.stderr.write('%s\n' % e)
            sys.stderr.write('Score volume for %s does not exist.\n' % structure)
            continue

    if common_shape:
        volumes_normalized, common_bbox = convert_vol_bbox_dict_to_overall_vol(vol_bbox_dict=volumes)

        if return_label_mappings:
            return volumes_normalized, common_bbox, structure_to_label, label_to_structure
        else:
            return volumes_normalized, common_bbox
    else:
        if return_label_mappings:
            return {k: crop_volume_to_minimal(vol=v, origin=o,
                        return_origin_instead_of_bbox=return_origin_instead_of_bbox)
                    for k, (v, o) in volumes.items()}, structure_to_label, label_to_structure

        else:
            return {k: crop_volume_to_minimal(vol=v, origin=o,
                        return_origin_instead_of_bbox=return_origin_instead_of_bbox)
                    for k, (v, o) in volumes.items()}


def get_domain_origin(stack, domain, resolution, loaded_cropbox_resolution='down32'):
    """
    Loads the 3D origin of a domain for a given stack.

    If specimen, the origin is wrt to wholebrain.
    If atlas, the origin is wrt to atlas space.

    Use this in combination with convert_frame_and_resolution().

    Args:
        domain (str): domain name
        resolution (str): output resolution
        loaded_cropbox_resolution (str): the resolution in which the loaded crop boxes are defined
    """

    out_resolution_um = convert_resolution_string_to_voxel_size(stack, resolution)

    if stack.startswith('atlas'):
        if domain == 'atlasSpace':
            origin_loadedResol = np.zeros((3,))
            loaded_cropbox_resolution_um = 0. # does not matter
        elif domain == 'canonicalAtlasSpace':
            origin_loadedResol = np.zeros((3,))
            loaded_cropbox_resolution_um = 0. # does not matter
        elif domain == 'atlasSpaceBrainstem': # obsolete?
            b = load_original_volume_bbox(stack=stack, volume_type='score',
                                    downscale=32,
                                      structure='7N_L')
            origin_loadedResol = b[[0,2,4]]
            loaded_cropbox_resolution_um = convert_resolution_string_to_voxel_size(stack='MD589', resolution='down32')
        else:
            raise
    else:

        print('loaded_cropbox_resolution', loaded_cropbox_resolution)
        loaded_cropbox_resolution_um = convert_resolution_string_to_voxel_size(resolution=loaded_cropbox_resolution, stack=stack)

        if domain == 'wholebrain':
            origin_loadedResol = np.zeros((3,))
        elif domain == 'wholebrainXYcropped':
            # alignedBrainstemCrop wrt. alignedPadded
            crop_xmin_rel2uncropped, crop_ymin_rel2uncropped = metadata_cache['cropbox'][stack][[0,2]]
            origin_loadedResol = np.array([crop_xmin_rel2uncropped, crop_ymin_rel2uncropped, 0])
        elif domain == 'brainstemXYfull':
            s1, s2 = metadata_cache['section_limits'][stack]
            crop_zmin_rel2uncropped = int(np.floor(np.mean(DataManager.convert_section_to_z(stack=stack, sec=s1, downsample=32, z_begin=0))))
            origin_loadedResol = np.array([0, 0, crop_zmin_rel2uncropped])
        elif domain == 'brainstem':
            crop_xmin_rel2uncropped, crop_ymin_rel2uncropped = metadata_cache['cropbox'][stack][[0,2]]
            s1, s2 = metadata_cache['section_limits'][stack]
            crop_zmin_rel2uncropped = int(np.floor(np.mean(DataManager.convert_section_to_z(stack=stack, sec=s1, downsample=32, z_begin=0))))
            origin_loadedResol = np.array([crop_xmin_rel2uncropped, crop_ymin_rel2uncropped, crop_zmin_rel2uncropped])
        elif domain == 'brainstemXYFullNoMargin':
            origin_loadedResol = np.loadtxt(DataManager.get_intensity_volume_bbox_filepath_v2(stack='MD589', prep_id=4, downscale=32)).astype(np.int)[[0,2,4]]
        else:
            raise "Domain %s is not recognized.\n" % domain

    origin_outResol = origin_loadedResol * loaded_cropbox_resolution_um / out_resolution_um

    return origin_outResol

def get_original_volume_basename(stack, prep_id=None, detector_id=None, resolution=None, downscale=None, structure=None, volume_type='score', **kwargs):
    """
    Args:
        resolution (str): down32 or 10.0um
    """

    components = []
    if prep_id is not None:
        components.append('prep%(prep)d' % {'prep':prep_id})
    if detector_id is not None:
        components.append('detector%(detector_id)d' % {'detector_id':detector_id})

    if resolution is None:
        if downscale is not None:
            resolution = 'down%d' % downscale

    if resolution is not None:
        components.append('%(outres)s' % {'outres':resolution})

    tmp_str = '_'.join(components)
    basename = '%(stack)s_%(tmp_str)s_%(volstr)s' % \
        {'stack':stack, 'tmp_str':tmp_str, 'volstr':volume_type_to_str(volume_type)}
    if structure is not None:
        basename += '_' + structure
    return basename

def get_volume_root_folder(stack):
    return os.path.join(VOLUME_ROOTDIR, stack)


def get_annotation_volume_bbox_filepath(stack, downscale=32):
    basename = get_original_volume_basename(volume_type='annotation', **locals())
    return os.path.join(get_volume_root_folder(stack), basename, basename + '_bbox.txt')

def get_score_volume_bbox_filepath_v3(stack_spec, structure, wrt='wholebrain'):

    if 'structure' not in stack_spec or stack_spec['structure'] is None:
        vol_basename = get_original_volume_basename_v2(stack_spec=stack_spec)
    else:
        stack_spec_no_structure = stack_spec.copy()
        stack_spec_no_structure['structure'] = None
        vol_basename = get_original_volume_basename_v2(stack_spec=stack_spec_no_structure)

    fp = os.path.join(VOLUME_ROOTDIR, '%(stack)s',
                      '%(basename)s',
                      'score_volumes',
                     '%(basename)s_%(struct)s_bbox' + ('_wrt_'+wrt if wrt is not None else '') + '.txt') % \
    {'stack':stack_spec['name'], 'basename':vol_basename, 'struct':structure}
    return fp

def get_score_volume_bbox_filepath(stack_spec, structure, wrt='wholebrain'):

    if 'structure' not in stack_spec or stack_spec['structure'] is None:
        vol_basename = get_original_volume_basename_v2(stack_spec=stack_spec)
    else:
        stack_spec_no_structure = stack_spec.copy()
        stack_spec_no_structure['structure'] = None
        vol_basename = get_original_volume_basename_v2(stack_spec=stack_spec_no_structure)

    fp = os.path.join(VOLUME_ROOTDIR, '%(stack)s',
                      '%(basename)s',
                      'score_volumes',
                     '%(basename)s_%(struct)s_bbox' + ('_wrt_'+wrt if wrt is not None else '') + '.txt') % \
    {'stack':stack_spec['name'], 'basename':vol_basename, 'struct':structure}
    return fp

def get_shell_bbox_filepath(stack, label, downscale):
    bbox_filepath = VOLUME_ROOTDIR + '/%(stack)s/%(stack)s_down%(ds)d_outerContourVolume_bbox.txt' % \
                    dict(stack=stack, ds=downscale)
    return bbox_filepath


def get_original_volume_bbox_filepath(stack,
                            detector_id=None,
                                      prep_id=None,
                            downscale=32,
                             volume_type='score',
                            structure=None, **kwargs):
    if volume_type == 'annotation':
        bbox_fn = get_annotation_volume_bbox_filepath(stack=stack)
    elif volume_type == 'score':
        bbox_fn = get_score_volume_bbox_filepath(**locals())
    elif volume_type == 'annotationAsScore':
        bbox_fn = get_score_volume_bbox_filepath(**locals())
    elif volume_type == 'shell':
        bbox_fn = get_shell_bbox_filepath(stack, structure, downscale)
    elif volume_type == 'thumbnail':
        bbox_fn = get_score_volume_bbox_filepath(stack=stack, structure='7N', downscale=downscale,
        detector_id=detector_id)
    else:
        raise Exception('Type must be annotation, score, shell or thumbnail.')

    return bbox_fn

def convert_section_to_z(sec, downsample=None, resolution=None, stack=None, mid=False, z_begin=None, first_sec=None):
    """
    Voxel size is determined by `resolution`.

    z = sec * section_thickness_in_unit_of_cubic_voxel_size - z_begin

    Physical size of a cubic voxel depends on the downsample factor.

    Args:
        downsample/resolution: this determines the voxel size.
        z_begin (float): z-coordinate of an origin. The z-coordinate of a given section is relative to this value.
            Default is the z position of the `first_sec`. This must be consistent with `downsample`.
        first_sec (int): Index of the section that defines z=0.
            Default is the first brainstem section defined in ``cropbox".
            If `stack` is given, the default is the first section of the brainstem.
            If `stack` is not given, default = 1.
        mid (bool): If false, return the z-coordinates of the two sides of the section. If true, only return a single scalar = the average.

    Returns:
        z1, z2 (2-tuple of float): the z-levels of the beginning and end of the queried section, counted from `z_begin`.
    """

    if downsample is not None:
        resolution = 'down%d' % downsample

    voxel_size_um = convert_resolution_string_to_voxel_size(resolution=resolution, stack=stack)
    section_thickness_in_voxel = SECTION_THICKNESS / voxel_size_um # Voxel size in z direction in unit of x,y pixel.
    # if first_sec is None:
    #     # first_sec, _ = DataManager.load_cropbox(stack)[4:]
    #     if stack is not None:
    #         first_sec = metadata_cache['section_limits'][stack][0]
    #     else:
    #         first_sec = 1
    #

    if z_begin is None:
        if first_sec is not None:
            z_begin = (first_sec - 1) * section_thickness_in_voxel
        else:
            z_begin = 0

    z1 = (sec-1) * section_thickness_in_voxel
    z2 = sec * section_thickness_in_voxel
    # print "z1, z2 =", z1, z2

    if mid:
        return np.mean([z1-z_begin, z2-1-z_begin])
    else:
        return z1-z_begin, z2-1-z_begin



def get_crop_bbox_rel2uncropped(stack):
    """
    Returns the bounding box of domain "brainstem" wrt domain "wholebrain".
    This assumes resolution of "down32".
    """

    crop_xmin_rel2uncropped, crop_xmax_rel2uncropped, \
    crop_ymin_rel2uncropped, crop_ymax_rel2uncropped, = metadata_cache['cropbox'][stack]

    s1, s2 = metadata_cache['section_limits'][stack]
    crop_zmin_rel2uncropped = int(np.floor(np.mean(convert_section_to_z(stack=stack, sec=s1, downsample=32, z_begin=0))))
    crop_zmax_rel2uncropped = int(np.ceil(np.mean(convert_section_to_z(stack=stack, sec=s2, downsample=32, z_begin=0))))

    crop_bbox_rel2uncropped = \
    np.array([crop_xmin_rel2uncropped, crop_xmax_rel2uncropped, \
    crop_ymin_rel2uncropped, crop_ymax_rel2uncropped, \
    crop_zmin_rel2uncropped, crop_zmax_rel2uncropped])
    return crop_bbox_rel2uncropped


def load_original_volume_bbox(stack, volume_type, prep_id=None, detector_id=None, structure=None, downscale=32,
                             relative_to_uncropped=False):
    """
    This returns the 3D bounding box of the volume.
    (?) Bounding box coordinates are with respect to coordinates origin of the contours. (?)

    Args:
        volume_type (str): score or annotationAsScore.
        relative_to_uncropped (bool): if True, the returned bounding box is with respect to "wholebrain"; if False, wrt "wholebrainXYcropped". Default is False.

    Returns:
        (6-tuple): bounding box of the volume (xmin, xmax, ymin, ymax, zmin, zmax).
    """

    bbox_fp = get_original_volume_bbox_filepath(**locals())
    # download_from_s3(bbox_fp)
    volume_bbox_wrt_wholebrainXYcropped = load_data(bbox_fp, filetype='bbox')
    # for volume type "score" or "thumbnail", bbox of the loaded volume wrt "wholebrainXYcropped".
    # for volume type "annotationAsScore", bbox on file is wrt wholebrain.

    if relative_to_uncropped:
        if volume_type == 'score' or volume_type == 'thumbnail':
            # bbox of "brainstem" wrt "wholebrain"
            brainstem_bbox_wrt_wholebrain = get_crop_bbox_rel2uncropped(stack=stack)
            volume_bbox_wrt_wholebrain = np.r_[volume_bbox_wrt_wholebrainXYcropped[:4] + brainstem_bbox_wrt_wholebrain[[0,0,2,2]], brainstem_bbox_wrt_wholebrain[4:]]
            return volume_bbox_wrt_wholebrain
        # else:
        #     continue
            # raise

    return volume_bbox_wrt_wholebrainXYcropped


def get_centroid_3d(v):
    """
    Compute the centroids of volumes.
    Args:
        v: volumes as 3d array, or dict of volumes, or dict of (volume, origin))
    """

    if isinstance(v, dict):
        centroids = {}
        for n, s in v.items():
            if isinstance(s, tuple): # volume, origin_or_bbox
                vol, origin_or_bbox = s
                if len(origin_or_bbox) == 3:
                    origin = origin_or_bbox
                elif len(origin_or_bbox) == 6:
                    bbox = origin_or_bbox
                    origin = bbox[[0,2,4]]
                else:
                    raise
                centroids[n] = np.mean(np.where(vol), axis=1)[[1,0,2]] + origin
            else: # volume
                centroids[n] = np.mean(np.where(s), axis=1)[[1,0,2]]
        return centroids
    else:
        return np.mean(np.where(v), axis=1)[[1,0,2]]

def load_alignment_results_v3(alignment_spec, what, reg_root_dir=REGISTRATION_PARAMETERS_ROOTDIR, out_form='dict'):
    """
    Args:
        what (str): any of parameters, scoreHistory, scoreEvolution or trajectory
    """
    INPUT_KEY_LOC = get_alignment_result_filepath_v3(alignment_spec=alignment_spec, what=what, reg_root_dir=reg_root_dir)
    with open(INPUT_KEY_LOC, 'r') as f:
        res = json.load(f)

    if what == 'parameters':
        tf_out = convert_transform_forms(transform=res, out_form=out_form)
        return tf_out
    else:
        return res

def get_alignment_result_filepath_v3(alignment_spec, what, reg_root_dir=REGISTRATION_PARAMETERS_ROOTDIR):
    """
    Args:
        what (str): any of parameters, scoreHistory/trajectory, scoreEvolution, parametersWeightedAverage
    """
    warp_basename = get_warped_volume_basename_v2(alignment_spec=alignment_spec)
    if what == 'parameters':
        ext = 'json'
    elif what == 'scoreHistory' or what == 'trajectory':
        ext = 'bp'
    elif what == 'scoreEvolution':
        ext = 'png'
    elif what == 'parametersWeightedAverage':
        ext = 'pkl'
    else:
        raise
    stack = alignment_spec['stack_m']['name']
    fp = os.path.join(reg_root_dir, stack, warp_basename, warp_basename + '_' + what + '.' + ext)
    print('get_alignment_result_filepath_v3', fp)
    return fp


#### registration utilities

def transform_points(pts, transform):
    '''
    Transform points.

    Args:
        pts:
        transform: any representation
    '''
    pts = list(pts)
    T = convert_transform_forms(transform=transform, out_form=(3,4))

    t = T[:, 3]
    A = T[:, :3]

    if len(np.atleast_2d(pts)) == 1:
            pts_prime = np.dot(A, np.array(pts).T) + t
    else:
        pts_prime = np.dot(A, np.array(pts).T) + t[:,None]

    return pts_prime.T


def convert_transform_forms(out_form, transform=None, aligner=None, select_best='last_value'):
    """
    Args:
        out_form: (3,4) or (4,4) or (12,) or "dict", "tuple"
    """

    if aligner is not None:
        centroid_m = aligner.centroid_m
        centroid_f = aligner.centroid_f

        if select_best == 'last_value':
            params = aligner.Ts[-1]
        elif select_best == 'max_value':
            params = aligner.Ts[np.argmax(aligner.scores)]
        else:
            raise Exception("select_best %s is not recognize." % select_best)
    else:
        if isinstance(transform, dict):
            if 'centroid_f_wrt_wholebrain' in transform:
                centroid_f = np.array(transform['centroid_f_wrt_wholebrain'])
                centroid_m = np.array(transform['centroid_m_wrt_wholebrain'])
                params = np.array(transform['parameters'])
            elif 'centroid_f' in transform:
                centroid_f = np.array(transform['centroid_f'])
                centroid_m = np.array(transform['centroid_m'])
                params = np.array(transform['parameters'])
            else:
                raise
        elif isinstance(transform, np.ndarray):
            if transform.shape == (12,):
                params = transform
                centroid_m = np.zeros((3,))
                centroid_f = np.zeros((3,))
            elif transform.shape == (3,4):
                params = transform.flatten()
                centroid_m = np.zeros((3,))
                centroid_f = np.zeros((3,))
            elif transform.shape == (4,4):
                params = transform[:3].flatten()
                centroid_m = np.zeros((3,))
                centroid_f = np.zeros((3,))
            else:
                raise
        else:
            raise Exception("Transform type %s is not recognized" % type(transform))

    T = consolidate(params=params, centroid_m=centroid_m, centroid_f=centroid_f)

    if out_form == (3,4):
        return T[:3]
    elif out_form == (4,4):
        return T
    elif out_form == (12,):
        return T[:3].flatten()
    elif out_form == 'dict':
        return dict(centroid_f_wrt_wholebrain = np.zeros((3,)),
                    centroid_m_wrt_wholebrain = np.zeros((3,)),
                    parameters = T[:3].flatten())
    elif out_form == 'tuple':
        return T[:3].flatten(), np.zeros((3,)), np.zeros((3,))
    else:
        raise Exception("Output form of %s is not recognized." % out_form)

    return T


def consolidate(params, centroid_m=(0,0,0), centroid_f=(0,0,0)):
    """
    Convert the set (parameter, centroid m, centroid f) to a single matrix.
    Args:
        params ((12,)-array):
        centroid_m ((3,)-array):
        centroid_f ((3,)-array):
    Returns:
        ((4,4)-array)
    """
    G = params.reshape((3,4))
    R = G[:3,:3]
    t = - np.dot(R, centroid_m) + G[:3,3] + centroid_f
    return np.vstack([np.c_[R,t], [0,0,0,1]])



def convert_to_original_name(name):
    return name.split('_')[0]


def convert_to_left_name(name):
    if name in singular_structures:
        # sys.stderr.write("Asked for left name for singular structure %s, returning itself.\n" % name)
        return name
    else:
        return convert_to_unsided_label(name) + '_L'

def convert_to_right_name(name):
    if name in singular_structures:
        # sys.stderr.write("Asked for right name for singular structure %s, returning itself.\n" % name)
        return name
    else:
        return convert_to_unsided_label(name) + '_R'


def fit_plane(X):
    """
    Fit a plane to a set of 3d points

    Parameters
    ----------
    X : n x 3 array
        points

    Returns
    ------
    normal : (3,) vector
        the normal vector of the plane
    c : (3,) vector
        a point on the plane
    """
    X = X[0][0]

    # http://math.stackexchange.com/questions/99299/best-fitting-plane-given-a-set-of-points
    # http://math.stackexchange.com/a/3871
    X = list(X)
    X = np.array(X)
    c = X.mean(axis=0)
    Xc = X - c
    U, _, VT = np.linalg.svd(Xc.T)
    return U[:,-1], c


def R_align_two_vectors(a, b):
    """
    Find the rotation matrix that align a onto b.
    """
    # http://math.stackexchange.com/questions/180418/calculate-rotation-matrix-to-align-vector-a-to-vector-b-in-3d/897677#897677

    v = np.cross(a, b)
    s = np.linalg.norm(v)
    c = np.dot(a, b)
    v_skew = np.array([[0, -v[2], v[1]],
                      [v[2], 0, -v[0]],
                      [-v[1], v[0], 0]])
    R = np.eye(3) + v_skew + np.dot(v_skew, v_skew)*(1-c)/(s + 1e-5)**2
    return R



def average_location(centroid_allLandmarks_wrt_fixedBrain=None, mean_centroid_allLandmarks_wrt_fixedBrain=None):
    """
    Compute the standardized centroid of every structure.

    This first estimates the mid-sagittal plane.
    Then find a standardized centroid for every structure, that is both closest to the population mean location and symmetric with respect to the mid-sagittal plane.

    Args:
        centroid_allLandmarks_wrt_fixedBrain (dict {str: (n,3)-array}): centroid of every structure instance wrt fixed brain
        mean_centroid_allLandmarks (dict {str: (3,)-array}): mean centroid of every structure instance wrt fixed brain

    Returns:
        standard_centroids_wrt_canonical: standardized locations of every structure, relative to the midplane anchor. Paired structures are symmetric relative to the mid-plane defined by centroid and normal.
        instance_centroids_wrt_canonical: the instance centroids in canonical atlas space
        midplane_anchor_wrt_fixedBrain: a point on the mid-sagittal plane that is used as the origin of canonical atlas space.
        midplane_normal: normal vector of the mid-sagittal plane estimated from centroids in original coordinates. Note that this is NOT the mid-plane normal using canonical coordinates, which by design should be (0,0,1).
        transform_matrix_to_atlasCanonicalSpace: (4,4) matrix that maps to canonical atlas space
        """

    if mean_centroid_allLandmarks_wrt_fixedBrain is None:
        mean_centroid_allLandmarks_wrt_fixedBrain = {name: np.mean(centroids, axis=0)
                                                     for name, centroids in
                                                     centroid_allLandmarks_wrt_fixedBrain.items()}

    names = set([convert_to_original_name(name_s) for name_s in mean_centroid_allLandmarks_wrt_fixedBrain.keys()])
    print('mean_centroid_allLandmarks_wrt_fixedBrain', mean_centroid_allLandmarks_wrt_fixedBrain)
    # Fit a midplane from the midpoints of symmetric landmark centroids
    midpoints_wrt_fixedBrain = {}
    for name in names:
        lname = convert_to_left_name(name)
        rname = convert_to_right_name(name)

        #         names = labelMap_unsidedToSided[name]

        #         # maybe ignoring singular instances is better
        #         if len(names) == 2:
        if lname in mean_centroid_allLandmarks_wrt_fixedBrain and rname in mean_centroid_allLandmarks_wrt_fixedBrain:
            midpoints_wrt_fixedBrain[name] = .5 * mean_centroid_allLandmarks_wrt_fixedBrain[lname] + .5 * \
                                             mean_centroid_allLandmarks_wrt_fixedBrain[rname]
        else:
            midpoints_wrt_fixedBrain[name] = mean_centroid_allLandmarks_wrt_fixedBrain[name]

    midplane_normal, midplane_anchor_wrt_fixedBrain = fit_plane(np.c_[midpoints_wrt_fixedBrain.values()])

    print('Mid-sagittal plane normal vector =', midplane_normal, '@ Mid-sagittal plane anchor wrt fixed wholebrain =',
          midplane_anchor_wrt_fixedBrain)

    R_fixedWholebrain_to_canonical = R_align_two_vectors(midplane_normal, (0, 0, 1))

    # points_midplane_oriented = {name: np.dot(R_to_canonical, p - midplane_anchor)
    #                             for name, p in mean_centroid_allLandmarks.iteritems()}

    transform_matrix_fixedWholebrain_to_atlasCanonicalSpace = consolidate(
        params=np.column_stack([R_fixedWholebrain_to_canonical, np.zeros((3,))]),
        centroid_m=midplane_anchor_wrt_fixedBrain,
        centroid_f=(0, 0, 0))

    print('Transform matrix to canonical atlas space =')
    print(transform_matrix_fixedWholebrain_to_atlasCanonicalSpace)

    print('Angular deviation of the mid sagittal plane normal around y axis (degree) =',
          np.rad2deg(np.arccos(midplane_normal[2])))

    points_midplane_oriented = {
        name: transform_points(p, transform=transform_matrix_fixedWholebrain_to_atlasCanonicalSpace)
        for name, p in mean_centroid_allLandmarks_wrt_fixedBrain.items()}

    if centroid_allLandmarks_wrt_fixedBrain is not None:

        instance_centroid_rel2atlasCanonicalSpace = \
            {n: transform_points(s, transform=transform_matrix_fixedWholebrain_to_atlasCanonicalSpace)
             for n, s in centroid_allLandmarks_wrt_fixedBrain.items()}
    else:
        instance_centroid_rel2atlasCanonicalSpace = None

    # Enforce symmetry

    canonical_locations = {}

    for name in names:

        lname = convert_to_left_name(name)
        rname = convert_to_right_name(name)

        if lname in points_midplane_oriented and rname in points_midplane_oriented:

            x, y, mz = .5 * points_midplane_oriented[lname] + .5 * points_midplane_oriented[rname]

            canonical_locations[lname] = np.r_[x, y, points_midplane_oriented[lname][2] - mz]
            canonical_locations[rname] = np.r_[x, y, points_midplane_oriented[rname][2] - mz]
        else:
            x, y, _ = points_midplane_oriented[name]
            canonical_locations[name] = np.r_[x, y, 0]

    return canonical_locations, instance_centroid_rel2atlasCanonicalSpace, \
           midplane_anchor_wrt_fixedBrain, midplane_normal, transform_matrix_fixedWholebrain_to_atlasCanonicalSpace


### plotting helpers for the atlas


def plot_centroid_means_and_covars_3d(instance_centroids,
                                        nominal_locations,
                                        canonical_centroid=None,
                                        canonical_normal=None,
                                      cov_mat_allStructures=None,
                                      radii_allStructures=None,
                                      ellipsoid_matrix_allStructures=None,
                                     colors=None,
                                     show_canonical_centroid=True,
                                     xlim=(0,400),
                                     ylim=(0,400),
                                     zlim=(0,400),
                                     xlabel='x',
                                     ylabel='y',
                                     zlabel='z',
                                     title='Centroid means and covariances'):
    """
    Plot the means and covariance matrices in 3D.
    All coordinates are relative to cropped MD589.
    Args:
        instance_centroids (dict {str: list of (3,)-arrays}): centroid coordinate of each instance relative to the canonical centroid
        nominal_locations (dict {str: (3,)-arrays}): the average centroid for all instance centroid of every structure relative to canonical centroid
        canonical_centroid ((3,)-arrays): coordinate of the origin of canonical frame, defined relative to atlas
        canonical_normal ((3,)-arrays): normal vector of the mid-sagittal plane. The mid-sagittal plane is supppose to pass the `canonical_centroid`.
        cov_mat_allStructures (dict {str: (3,3)-ndarray}): covariance_matrices
        radii_allStructures (dict {str: (3,)-ndarray}): radius of each axis
        ellipsoid_matrix_allStructures (dict {str: (3,3)-ndarray}): Of each matrix, each row is a eigenvector of the corresponding covariance matrix
        colors (dict {str: 3-tuple}): for example: {'7N': (1,0,0)}.
    """

    # Load ellipsoid: three radius and axes.
    if radii_allStructures is not None and ellipsoid_matrix_allStructures is not None:
        pass
    elif cov_mat_allStructures is not None:
        radii_allStructures, ellipsoid_matrix_allStructures = compute_ellipsoid_from_covar(cov_mat_allStructures)
    else:
        _, radii_allStructures, ellipsoid_matrix_allStructures = compute_covar_from_instance_centroids(instance_centroids)

    # Plot in 3D.

    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure(figsize=(20, 20))
    ax = fig.add_subplot(111, projection='3d')

    if colors is None:
        colors = {name_s: (0,0,1) for name_s in instance_centroids}

    for name_s, centroids in instance_centroids.items():
    #     if name_s == '7N_L' or name_s == '7N_R':

        if canonical_centroid is None:
            centroids2 = np.array(centroids)
        else:
            centroids2 = np.array(centroids) + canonical_centroid

        ax.scatter(centroids2[:,0], centroids2[:,1], centroids2[:,2],
                   marker='o', s=100, alpha=.1, color=colors[name_s])

        if canonical_centroid is None:
            c = nominal_locations[name_s]
        else:
            c = nominal_locations[name_s] + canonical_centroid

        ax.scatter(c[0], c[1], c[2],
                   color=colors[name_s], marker='*', s=100)

        # Plot uncerntainty ellipsoids
        u = np.linspace(0.0, 2.0 * np.pi, 100)
        v = np.linspace(0.0, np.pi, 100)
        x = radii_allStructures[name_s][0] * np.outer(np.cos(u), np.sin(v))
        y = radii_allStructures[name_s][1] * np.outer(np.sin(u), np.sin(v))
        z = radii_allStructures[name_s][2] * np.outer(np.ones_like(u), np.cos(v))
        for i in range(len(u)):
            for j in range(len(v)):
                [x[i,j],y[i,j],z[i,j]] = np.dot([x[i,j],y[i,j],z[i,j]], ellipsoid_matrix_allStructures[name_s]) + c

    #     ax.plot_surface(x, y, z, color='b')
        ax.plot_wireframe(x, y, z,  rstride=4, cstride=4, color='b', alpha=0.2)

    if canonical_centroid is not None:
        if show_canonical_centroid:
            ax.scatter(canonical_centroid[0], canonical_centroid[1], canonical_centroid[2],
               color=(0,0,0), marker='^', s=200)

        # Plot mid-sagittal plane
        if canonical_normal is not None:
            canonical_midplane_xx, canonical_midplane_yy = np.meshgrid(range(xlim[0], xlim[1], 100), range(ylim[0], ylim[1], 100), indexing='xy')
            canonical_midplane_z = -(canonical_normal[0]*(canonical_midplane_xx-canonical_centroid[0]) + \
            canonical_normal[1]*(canonical_midplane_yy-canonical_centroid[1]) + \
            canonical_normal[2]*(-canonical_centroid[2]))/canonical_normal[2]
            ax.plot_surface(canonical_midplane_xx, canonical_midplane_yy, canonical_midplane_z, alpha=.1)
    else:
        sys.stderr.write("canonical_centroid not provided. Skip plotting cenonical centroid and mid-sagittal plane.\n")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    # ax.set_axis_off()
    ax.set_xlim3d([xlim[0], xlim[1]]);
    ax.set_ylim3d([ylim[0], ylim[1]]);
    ax.set_zlim3d([zlim[0], zlim[1]]);
    # ax.view_init(azim = 90 + 20,elev = 0 - 20)
    ax.view_init(azim = 270, elev = 0)

    # Hide y-axis (https://stackoverflow.com/questions/12391271/matplotlib-turn-off-z-axis-only-in-3-d-plot)
    ax.w_yaxis.line.set_lw(0.)
    ax.set_yticks([])

    ax.set_aspect(1.0)
    ax.set_title(title)
    plt.legend()
    plt.show()


def compute_ellipsoid_from_covar(covar_mat):
    """
    Compute the ellipsoid (three radii and three axes) of each structure from covariance matrices.
    Radii are the square root of the singular values (or 1 sigma).
    Returns:
        dict {str: (3,)-ndarray}: radius of each axis
        dict {str: (3,3)-ndarray}: Of each matrix, each row is a eigenvector of the corresponding covariance matrix
    """

    radii_allStructures = {}
    ellipsoid_matrix_allStructures = {}
    for name_s, cov_mat in sorted(covar_mat.items()):
        u, s, vt = np.linalg.svd(cov_mat)
    #     print name_s, u[:,0], u[:,1], u[:,2],
        radii_allStructures[name_s] = np.sqrt(s)
        ellipsoid_matrix_allStructures[name_s] = vt
    return radii_allStructures, ellipsoid_matrix_allStructures

def compute_covar_from_instance_centroids(instance_centroids):
    """
    Compute the covariance matrices based on instance centroids.
    Args:
        instance_centroids: dict {str: list of (3,)-arrays}
    Returns:
        dict {str: (3,3)-ndarray}: covariance_matrices
        dict {str: (3,)-ndarray}: radius of each axis
        dict {str: (3,3)-ndarray}: Of each matrix, each row is a eigenvector of the corresponding covariance matrix
    """

    cov_mat_allStructures = {}
    radii_allStructures = {}
    ellipsoid_matrix_allStructures = {}
    for name_s, centroids in sorted(instance_centroids.items()):
        centroids2 = np.array(centroids)
        cov_mat = np.cov(centroids2.T)
        cov_mat_allStructures[name_s] = cov_mat
        u, s, vt = np.linalg.svd(cov_mat)
    #     print name_s, u[:,0], u[:,1], u[:,2],
        radii_allStructures[name_s] = np.sqrt(s)
        ellipsoid_matrix_allStructures[name_s] = vt

    return cov_mat_allStructures, radii_allStructures, ellipsoid_matrix_allStructures



############## Colors ##############

boynton_colors = dict(blue=(0,0,255),
    red=(255,0,0),
    green=(0,255,0),
    yellow=(255,255,0),
    magenta=(255,0,255),
    pink=(255,128,128),
    gray=(128,128,128),
    brown=(128,0,0),
    orange=(255,128,0))

kelly_colors = dict(vivid_yellow=(255, 179, 0),
                    strong_purple=(128, 62, 117),
                    vivid_orange=(255, 104, 0),
                    very_light_blue=(166, 189, 215),
                    vivid_red=(193, 0, 32),
                    grayish_yellow=(206, 162, 98),
                    medium_gray=(129, 112, 102),

                    # these aren't good for people with defective color vision:
                    vivid_green=(0, 125, 52),
                    strong_purplish_pink=(246, 118, 142),
                    strong_blue=(0, 83, 138),
                    strong_yellowish_pink=(255, 122, 92),
                    strong_violet=(83, 55, 122),
                    vivid_orange_yellow=(255, 142, 0),
                    strong_purplish_red=(179, 40, 81),
                    vivid_greenish_yellow=(244, 200, 0),
                    strong_reddish_brown=(127, 24, 13),
                    vivid_yellowish_green=(147, 170, 0),
                    deep_yellowish_brown=(89, 51, 21),
                    vivid_reddish_orange=(241, 58, 19),
                    dark_olive_green=(35, 44, 22))

#high_contrast_colors = boynton_colors.values() + kelly_colors.values()
bc = list(boynton_colors.values())
kc = list(kelly_colors.values())
high_contrast_colors  = bc + kc
hc_perm = [ 0,  5, 28, 26, 12, 11,  4,  8, 25, 22,  3,  1, 20, 19, 27, 13, 24,
       17, 16, 15,  7, 14, 21, 18, 23,  2, 10,  9,  6]
high_contrast_colors = [high_contrast_colors[i] for i in hc_perm]


paired_structures = ['5N', '6N', '7N', '7n', 'Amb', 'LC', 'LRt', 'Pn', 'Tz', 'VLL', 'RMC', 'SNC', 'SNR', '3N', '4N',
                    'Sp5I', 'Sp5O', 'Sp5C', 'PBG', '10N', 'VCA', 'VCP', 'DC']
# singular_structures = ['AP', '12N', 'RtTg', 'sp5', 'outerContour', 'SC', 'IC']
singular_structures = ['AP', '12N', 'RtTg', 'SC', 'IC']
singular_structures_with_side_suffix = ['AP_S', '12N_S', 'RtTg_S', 'SC_S', 'IC_S']
all_known_structures = paired_structures + singular_structures
all_known_structures_sided = sum([[n] if n in singular_structures
                        else [convert_to_left_name(n), convert_to_right_name(n)]
                        for n in all_known_structures], [])


name_sided_to_color = {s: high_contrast_colors[i%len(high_contrast_colors)]
                     for i, s in enumerate(all_known_structures_sided) }
name_sided_to_color_float = {s: np.array(c)/255. for s, c in name_sided_to_color.items()}

name_unsided_to_color = {s: high_contrast_colors[i%len(high_contrast_colors)]
                     for i, s in enumerate(all_known_structures) }
name_unsided_to_color_float = {s: np.array(c)/255. for s, c in name_unsided_to_color.items()}

#stack_to_color = {n: high_contrast_colors[i%len(high_contrast_colors)] for i, n in enumerate(all_stacks)}
#stack_to_color_float = {s: np.array(c)/255. for s, c in stack_to_color.iteritems()}

name_unsided_to_color = {s: high_contrast_colors[i%len(high_contrast_colors)]
                     for i, s in enumerate(all_known_structures) }

# Load all structures
paired_structures = ['5N', '6N', '7N', '7n', 'Amb', 'LC', 'LRt', 'Pn', 'Tz', 'VLL', 'RMC', \
                     'SNC', 'SNR', '3N', '4N', 'Sp5I', 'Sp5O', 'Sp5C', 'PBG', '10N', 'VCA', 'VCP', 'DC']
# singular_structures = ['AP', '12N', 'RtTg', 'sp5', 'outerContour', 'SC', 'IC']
singular_structures = ['AP', '12N', 'RtTg', 'SC', 'IC']

# Make a list of all structures INCLUDING left and right variants
all_structures_total = list(singular_structures)
rh_structures = []
lh_structures = []
for structure in paired_structures:
    all_structures_total.append(structure + '_R')
    all_structures_total.append(structure + '_L')
    rh_structures.append(structure + '_R')
    lh_structures.append(structure + '_L')

def get_structure_mean_positions_filepath(atlas_name, resolution, **kwargs):
    """
    Filepath of the structure mean positions.
    """
    MESH_ROOTDIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_meshes'
    return os.path.join(MESH_ROOTDIR, atlas_name, atlas_name + '_' + resolution + '_meanPositions.pkl')

"""
def save_data(data, fp, upload_s3=True):
    import bloscpack as bp

    from vis3d_utilities import save_mesh_stl

    os.makedirs(os.path.dirname(fp), exist_ok=True)

    if fp.endswith('.bp'):
        try:
            bp.pack_ndarray_file(np.ascontiguousarray(data), fp)
            # ascontiguousarray is important, without which sometimes the loaded array will be different from saved.
        except:
            fp = fp.replace('.bp','.npy')
            np.save( fp, np.ascontiguousarray(data))
    elif fp.endswith('.npy'):
        np.save( fp, np.ascontiguousarray(data))
    elif fp.endswith('.json'):
        save_json(data, fp)
    elif fp.endswith('.pkl'):
        save_pickle(data, fp)
    elif fp.endswith('.hdf'):
        save_hdf_v2(data, fp)
    elif fp.endswith('.stl'):
        save_mesh_stl(data, fp)
    elif fp.endswith('.txt'):
        if isinstance(data, np.ndarray):
            np.savetxt(fp, data)
        else:
            raise
    elif fp.endswith('.dump'): # sklearn classifiers
        import joblib
        joblib.dump(data, fp)
    elif fp.endswith('.png') or fp.endswith('.tif') or fp.endswith('.jpg'):
        io.imsave(fp, data)
    else:
        raise
"""

def parallel_where_binary(binary_volume, num_samples=None):
    """
    Returns:
        (n,3)-ndarray
    """

    w = np.where(binary_volume)

    if num_samples is not None:
        n = len(w[0])
        sample_indices = np.random.choice(range(n), min(num_samples, n), replace=False)
        return np.c_[w[1][sample_indices].astype(np.int16),
                     w[0][sample_indices].astype(np.int16),
                     w[2][sample_indices].astype(np.int16)]
    else:
        return np.c_[w[1].astype(np.int16), w[0].astype(np.int16), w[2].astype(np.int16)]


def compute_bspline_cp_contribution_to_test_pts(control_points, test_points):
    """
    Args:
        control_points (1d-array): normalized in the unit of spacing interval
        test_points (1d-array): normalized in the unit of spacing interval
    """

    test_points_x_normalized = test_points
    ctrl_point_x_normalized = control_points

    D = np.subtract.outer(test_points_x_normalized, ctrl_point_x_normalized) # (#testpts, #ctrlpts)

    in_1 = ((D >= 0) & (D < 1)).astype(np.int)
    in_2 = ((D >= 1) & (D < 2)).astype(np.int)
    in_3 = ((D >= 2) & (D < 3)).astype(np.int)
    in_4 = ((D >= 3) & (D < 4)).astype(np.int)
    F = in_1 * D**3/6. + \
    in_2 * (D**2*(2-D)/6. + D*(3-D)*(D-1)/6. + (4-D)*(D-1)**2/6.) + \
    in_3 * (D*(3-D)**2/6. + (4-D)*(3-D)*(D-1)/6. + (4-D)**2*(D-2)/6.) + \
    in_4 * (4-D)**3/6.

    return F.T # (#ctrl, #test)


def convert_volume_forms(volume, out_form):
    """
    Convert a (volume, origin) tuple into a bounding box.
    """

    if isinstance(volume, np.ndarray):
        vol = volume
        ori = np.zeros((3,))
    elif isinstance(volume, tuple):
        assert len(volume) == 2
        vol = volume[0]
        if len(volume[1]) == 3:
            ori = volume[1]
        elif len(volume[1]) == 6:
            ori = volume[1][[0,2,4]]
        else:
            raise

    bbox = np.array([ori[0], ori[0] + vol.shape[1]-1, ori[1], ori[1] + vol.shape[0]-1, ori[2], ori[2] + vol.shape[2]-1])

    if out_form == ("volume", 'origin'):
        return (vol, ori)
    elif out_form == ("volume", 'bbox'):
        return (vol, bbox)
    elif out_form == "volume":
        return vol
    else:
        raise Exception("out_form %s is not recognized.")


def transform_points_affine(T, pts=None, c=(0,0,0), pts_centered=None, c_prime=(0,0,0)):
    '''
    Transform points by a rigid or affine transform.

    Args:
        T ((nparams,)-ndarray): flattened array of transform parameters.
        c ((3,)-ndarray): origin of input points
        c_prime((3,)-ndarray): origin of output points
        pts ((n,3)-ndararay): coodrinates of input points
    '''

    if pts_centered is None:
        assert pts is not None
        pts_centered = pts - c

    Tm = np.reshape(T, (3,4))
    t = Tm[:, 3]
    A = Tm[:, :3]
    pts_prime = np.dot(A, pts_centered.T) + (t + c_prime)[:,None]

    return pts_prime.T


def compute_gradient_v2(volume, smooth_first=False, dtype=np.float16):
    """
    Args:
        volume
        smooth_first (bool): If true, smooth each volume before computing gradients.
        This is useful if volume is binary and gradients are only nonzero at structure borders.
    Note:
        # 3.3 second - re-computing is much faster than loading
        # .astype(np.float32) is important;
        # Otherwise the score volume is type np.float16, np.gradient requires np.float32 and will have to convert which is very slow
        # 2s (float32) vs. 20s (float16)
    """

    if isinstance(volume, dict):

        # gradients = {}
        # for ind, (v, o) in volumes.iteritems():
        #     print "Computing gradient for", ind
        #     # t1 = time.time()
        #     gradients[ind] = (compute_gradient_v2((v, o), smooth_first=smooth_first), o)
        #     # sys.stderr.write("Overall: %.2f seconds.\n" % (time.time()-t1))

        gradients = {ind: compute_gradient_v2((v, o), smooth_first=smooth_first)
                     for ind, (v, o) in volume.items()}

        return gradients

    else:
        v, o = convert_volume_forms(volume, out_form=("volume", "origin"))

        g = np.zeros((3,) + v.shape)

        # t = time.time()
        cropped_v, (xmin,xmax,ymin,ymax,zmin,zmax) = crop_volume_to_minimal(v, margin=5, return_origin_instead_of_bbox=False)
        # sys.stderr.write("Crop: %.2f seconds.\n" % (time.time()-t))

        if smooth_first:
            # t = time.time()
            cropped_v = gaussian(cropped_v, 3)
            # sys.stderr.write("Smooth: %.2f seconds.\n" % (time.time()-t))

        # t = time.time()
        cropped_v_gy_gx_gz = np.gradient(cropped_v.astype(np.float32), 3, 3, 3)
        # sys.stderr.write("Compute gradient: %.2f seconds.\n" % (time.time()-t))

        g[0][ymin:ymax+1, xmin:xmax+1, zmin:zmax+1] = cropped_v_gy_gx_gz[1]
        g[1][ymin:ymax+1, xmin:xmax+1, zmin:zmax+1] = cropped_v_gy_gx_gz[0]
        g[2][ymin:ymax+1, xmin:xmax+1, zmin:zmax+1] = cropped_v_gy_gx_gz[2]

        return g.astype(dtype), o


def transform_points_bspline(buvwx, buvwy, buvwz,
                             volume_shape=None, interval=None,
                             ctrl_x_intervals=None,
                             ctrl_y_intervals=None,
                             ctrl_z_intervals=None,
                             pts=None, c=(0,0,0), pts_centered=None, c_prime=(0,0,0),
                            NuNvNw_allTestPts=None):
    """
    Transform points by a B-spline transform.

    Args:
        volume_shape ((3,)-ndarray of int): (xdim, ydim, zdim)
        interval (int): control point spacing in x,y,z directions.
        pts ((n,3)-ndarray): input point coordinates.
        NuNvNw_allTestPts ((n_test, n_ctrlx * n_ctrly * n_ctrlz)-array)

    Returns:
        transformed_pts ((n,3)-ndarray): transformed point coordinates.
    """

    if pts_centered is None:
        assert pts is not None
        pts_centered = pts - c

    if NuNvNw_allTestPts is None:

        xdim, ydim, zdim = volume_shape
        if ctrl_x_intervals is None:
            ctrl_x_intervals = np.arange(0, xdim, interval)
        if ctrl_y_intervals is None:
            ctrl_y_intervals = np.arange(0, ydim, interval)
        if ctrl_z_intervals is None:
            ctrl_z_intervals = np.arange(0, zdim, interval)

        ctrl_x_intervals_centered = ctrl_x_intervals - c[0]
        ctrl_y_intervals_centered = ctrl_y_intervals - c[1]
        ctrl_z_intervals_centered = ctrl_z_intervals - c[2]

        t = time.time()

        NuPx_allTestPts = compute_bspline_cp_contribution_to_test_pts(control_points=ctrl_x_intervals_centered/float(interval),
                                                                     test_points=pts_centered[:,0]/float(interval))
        NvPy_allTestPts = compute_bspline_cp_contribution_to_test_pts(control_points=ctrl_y_intervals_centered/float(interval),
                                                                     test_points=pts_centered[:,1]/float(interval))
        NwPz_allTestPts = compute_bspline_cp_contribution_to_test_pts(control_points=ctrl_z_intervals_centered/float(interval),
                                                                     test_points=pts_centered[:,2]/float(interval))

#         NuPx_allTestPts = np.array([[N(ctrl_x/float(interval), x/float(interval)) for testPt_i, (x, y, z) in enumerate(pts_centered)]
#                                     for ctrlXInterval_i, ctrl_x in enumerate(ctrl_x_intervals_centered)])

#         NvPy_allTestPts = np.array([[N(ctrl_y/float(interval), y/float(interval)) for testPt_i, (x, y, z) in enumerate(pts_centered)]
#                                     for ctrlYInterval_i, ctrl_y in enumerate(ctrl_y_intervals_centered)])

#         NwPz_allTestPts = np.array([[N(ctrl_z/float(interval), z/float(interval)) for testPt_i, (x, y, z) in enumerate(pts_centered)]
#                                     for ctrlZInterval_i, ctrl_z in enumerate(ctrl_z_intervals_centered)])

        sys.stderr.write("Compute NuPx/NvPy/NwPz: %.2f seconds.\n" % (time.time() - t))

        # print NuPx_allTestPts.shape, NvPy_allTestPts.shape, NwPz_allTestPts.shape
        # (9, 157030) (14, 157030) (8, 157030)
        # (n_ctrlx, n_test)

        t = time.time()

        NuNvNw_allTestPts = np.einsum('it,jt,kt->ijkt', NuPx_allTestPts, NvPy_allTestPts, NwPz_allTestPts).reshape((-1, NuPx_allTestPts.shape[-1])).T

        # NuNvNw_allTestPts = np.array([np.ravel(np.tensordot(np.tensordot(NuPx_allTestPts[:,testPt_i],
        #                                                                  NvPy_allTestPts[:,testPt_i], 0),
        #                                                     NwPz_allTestPts[:,testPt_i], 0))
        #                           for testPt_i in range(len(pts_centered))])
        sys.stderr.write("Compute NuNvNw: %.2f seconds.\n" % (time.time() - t))

    # the expression inside np.ravel gives array of shape (n_ctrlx, n_ctrly, nctrlz)

    # print NuNvNw_allTestPts.shape
    # (157030, 1008)
    # (n_test, n_ctrlx * n_ctrly * n_ctrlz)

    # t = time.time()
    sum_uvw_NuNvNwbuvwx = np.dot(NuNvNw_allTestPts, buvwx)
    sum_uvw_NuNvNwbuvwy = np.dot(NuNvNw_allTestPts, buvwy)
    sum_uvw_NuNvNwbuvwz = np.dot(NuNvNw_allTestPts, buvwz)
    # sys.stderr.write("Compute sum: %.2f seconds.\n" % (time.time() - t))

    # print sum_uvw_NuNvNwbuvwx.shape

    transformed_pts = pts_centered + np.c_[sum_uvw_NuNvNwbuvwx, sum_uvw_NuNvNwbuvwy, sum_uvw_NuNvNwbuvwz] + c_prime
    return transformed_pts


def rotate_transform_vector(v, theta_xy=0,theta_yz=0,theta_xz=0,c=(0,0,0)):
    """
    v is 12-length parameter.
    """
    cos_theta_z = np.cos(theta_xy)
    sin_theta_z = np.sin(theta_xy)
    Rz = np.array([[cos_theta_z, -sin_theta_z, 0], [sin_theta_z, cos_theta_z, 0], [0, 0, 1]])
    cos_theta_x = np.cos(theta_yz)
    sin_theta_x = np.sin(theta_yz)
    Rx = np.array([[1, 0, 0], [0, cos_theta_x, -sin_theta_x], [0, sin_theta_x, cos_theta_x]])
    cos_theta_y = np.cos(theta_xz)
    sin_theta_y = np.sin(theta_xz)
    Ry = np.array([[cos_theta_y, 0, -sin_theta_y], [0, 1, 0], [sin_theta_y, 0, cos_theta_y]])

    R = np.zeros((3,3))
    R[0, :3] = v[:3]
    R[1, :3] = v[4:7]
    R[2, :3] = v[8:11]
    t = v[[3,7,11]]
    R_new = np.dot(Rx, np.dot(Ry, np.dot(Rz, R)))
    t_new = t + c - np.dot(R_new, c)
    return np.ravel(np.c_[R_new, t_new])


def affine_components_to_vector(tx=0,ty=0,tz=0,theta_xy=0,theta_xz=0,theta_yz=0,c=(0,0,0)):
    """
    y = R(x-c)+t+c.

    Args:
        theta_xy (float): in radian.
    Returns:
        (12,)-ndarray:
    """
    # assert np.count_nonzero([theta_xy, theta_yz, theta_xz]) <= 1, \
    # "Current implementation is sound only if only one rotation is given."

    cos_theta_xy = np.cos(theta_xy)
    sin_theta_xy = np.sin(theta_xy)
    cos_theta_yz = np.cos(theta_yz)
    sin_theta_yz = np.sin(theta_yz)
    cos_theta_xz = np.cos(theta_xz)
    sin_theta_xz = np.sin(theta_xz)
    Rz = np.array([[cos_theta_xy, -sin_theta_xy, 0], [sin_theta_xy, cos_theta_xy, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cos_theta_yz, -sin_theta_yz], [0, sin_theta_yz, cos_theta_yz]])
    Ry = np.array([[cos_theta_xz, 0, -sin_theta_xz], [0, 1, 0], [sin_theta_xz, 0, cos_theta_xz]])
    R = np.dot(Rx, np.dot(Ry, Rz))
    tt = np.r_[tx,ty,tz] + c - np.dot(R,c)
    return np.ravel(np.c_[R, tt])


def compose_alignment_parameters(list_of_transform_parameters):
    """
    Args:
        list_of_transform_parameters: the transforms are applied in the order from left to right.

    Returns:
        (4,4)-array: transform matrix that maps wholebrain domain of moving brain to wholebrain domain of fixed brain.
    """

    T0 = np.eye(4)

    for transform_parameters in list_of_transform_parameters:
        T = convert_transform_forms(out_form=(4, 4), transform=transform_parameters)

        #         if isinstance(transform_parameters, dict):
        #             # cf = np.array(transform_parameters['centroid_f'])
        #             # cm = np.array(transform_parameters['centroid_m'])
        #             # of = np.array(transform_parameters['domain_f_origin_wrt_wholebrain'])
        #             # om = np.array(transform_parameters['domain_m_origin_wrt_wholebrain'])
        #             # params = np.array(transform_parameters['parameters'])
        #             # T = consolidate(params=params, centroid_m=cm+om, centroid_f=cf+of)

        #             cf = np.array(transform_parameters['centroid_f_wrt_wholebrain'])
        #             cm = np.array(transform_parameters['centroid_m_wrt_wholebrain'])
        #             params = np.array(transform_parameters['parameters'])
        #             T = consolidate(params=params, centroid_m=cm, centroid_f=cf)
        #         elif transform_parameters.shape == (3,4):
        #             T = np.vstack([transform_parameters, [0,0,0,1]])
        #         elif transform_parameters.shape == (12,):
        #             T = np.vstack([transform_parameters.reshape((3,4)), [0,0,0,1]])
        #         elif transform_parameters.shape == (4,4):
        #             T = transform_parameters
        #         else:
        #             print transform_parameters.shape
        #             raise

        T0 = np.dot(T, T0)

    return T0


def rotationMatrixToEulerAngles(R) :
    """
    Calculates rotation matrix to euler angles
    The result is the same as MATLAB except the order
    of the euler angles ( x and z are swapped ).
    Ref: https://www.learnopencv.com/rotation-matrix-to-euler-angles/
    """
    sy = np.sqrt(R[0,0] * R[0,0] +  R[1,0] * R[1,0])
    singular = sy < 1e-6

    if  not singular :
        x = np.arctan2(R[2,1] , R[2,2])
        y = np.arctan2(-R[2,0], sy)
        z = np.arctan2(R[1,0], R[0,0])
    else :
        x = np.arctan2(-R[1,2], R[1,1])
        y = np.arctan2(-R[2,0], sy)
        z = 0

    return np.array([x, y, z])


def eulerAnglesToRotationMatrix(theta):
    """
    Calculates Rotation Matrix given euler angles.
    """

    R_x = np.array([[1,         0,                  0                   ],
                    [0,         np.cos(theta[0]), -np.sin(theta[0]) ],
                    [0,         np.sin(theta[0]), np.cos(theta[0])  ]
                    ])
    R_y = np.array([[np.cos(theta[1]),    0,      np.sin(theta[1])  ],
                    [0,                     1,      0                   ],
                    [-np.sin(theta[1]),   0,      np.cos(theta[1])  ]
                    ])
    R_z = np.array([[np.cos(theta[2]),    -np.sin(theta[2]),    0],
                    [np.sin(theta[2]),    np.cos(theta[2]),     0],
                    [0,                     0,                      1]
                    ])
    R = np.dot(R_z, np.dot( R_y, R_x ))
    return R

