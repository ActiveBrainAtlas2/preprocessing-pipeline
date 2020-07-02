import os
import sys
from multiprocessing.pool import Pool

import numpy as np
from pandas import read_hdf
from skimage import io
import json
from collections import defaultdict
import re
from skimage.measure import find_contours, regionprops

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.sqlcontroller import SqlController
from utilities.alignment_utility import load_hdf, one_liner_to_arr, load_ini, convert_resolution_string_to_um
from utilities.file_location import VOLUME_DIR as VOLUME_ROOTDIR, FileLocationManager
from utilities.coordinates_converter import CoordinatesConverter

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
    sqlController = SqlController()
    sqlController.get_animal_info(stack)

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
    filename = os.path.join(VOLUME_ROOTDIR, alignment_spec['stack_m']['name'],
                            vol_basename, 'score_volumes', vol_basename_with_structure_suffix + '.npy')
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
