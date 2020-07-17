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
from utilities.alignment_utility import load_hdf, one_liner_to_arr, load_ini, convert_resolution_string_to_um, convert_resolution_string_to_voxel_size
from utilities.file_location import CSHL_DIR as VOLUME_ROOTDIR, FileLocationManager
from utilities.coordinates_converter import CoordinatesConverter
SECTION_THICKNESS = 20. # in um
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
        vol_bbox_dict = {k: (v, (o[0], o[0]+v.shape[1]-1, o[1], o[1]+v.shape[0]-1, o[2], o[2]+v.shape[2]-1)) for k,(v,o) in vol_origin_dict.iteritems()}

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
    from registration_utilities import convert_transform_forms
    res = load_data(DataManager.get_alignment_result_filepath_v3(alignment_spec=alignment_spec, what=what, reg_root_dir=reg_root_dir))
    if what == 'parameters':
        tf_out = convert_transform_forms(transform=res, out_form=out_form)
        return tf_out
    else:
        return res
