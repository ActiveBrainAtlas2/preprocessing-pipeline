import json
import sys
import os
from collections import defaultdict
import cv2
from skimage import io
import matplotlib
import argparse
from skimage.color import gray2rgb
matplotlib.use('Agg')  # https://stackoverflow.com/a/3054314
import numpy as np

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.coordinates_converter import CoordinatesConverter
from utilities.alignment_utility import convert_resolution_string_to_um
from utilities.imported_atlas_utilities import find_contour_points_3d, convert_to_unsided_label, load_json, \
    SECTION_THICKNESS, load_transformed_volume_v2, REGISTRATION_PARAMETERS_ROOTDIR
from utilities.file_location import FileLocationManager

LEVEL_TO_COLOR_LINE = {0.1: (125,0,125), 0.25: (0,255,0), 0.5: (255,0,0), 0.75: (0,125,0), 0.99: (0,0,255)}

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
    fileLocationManager = FileLocationManager(stack)
    structure_contours_wrt_alignedBrainstemCrop_rawResol = defaultdict(lambda: defaultdict(dict))
    INPUT = os.listdir(os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_aligned'))
    len_files = len(os.listdir(INPUT))
    section_list = [i for i in range(1, len_files+1)]
    converter = CoordinatesConverter(stack=stack, section_list=section_list)

    converter.register_new_resolution('structure_volume', resol_um=convert_resolution_string_to_um(stack=stack,
                                      resolution=resolution))
    converter.register_new_resolution('image', resol_um=convert_resolution_string_to_um(resolution='raw', stack=stack))

    for name_s, (structure_volume_volResol, origin_wrt_wholebrain_volResol) in volumes.items():

        converter.derive_three_view_frames(name_s,
                                           origin_wrt_wholebrain_um=convert_resolution_string_to_um(stack=stack,
                                                                                                    resolution=resolution) * origin_wrt_wholebrain_volResol,
                                           zdim_um=convert_resolution_string_to_um(stack=stack, resolution=resolution) *
                                                   structure_volume_volResol.shape[2])

        positions_of_all_sections_wrt_structureVolume = converter.convert_frame_and_resolution(
            p=np.array(sections)[:, None],
            in_wrt=('wholebrain', 'sagittal'), in_resolution='section',
            out_wrt=(name_s, 'sagittal'), out_resolution='structure_volume')[..., 2].flatten()

        structure_ddim = structure_volume_volResol.shape[2]

        valid_mask = (positions_of_all_sections_wrt_structureVolume >= 0) & (
                    positions_of_all_sections_wrt_structureVolume < structure_ddim)
        if np.count_nonzero(valid_mask) == 0:
            #             sys.stderr.write("%s, valid_mask is empty.\n" % name_s)
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
                    out_wrt=('wholebrainXYcropped', 'sagittal'), out_resolution='image_image_section')

                assert len(np.unique(contour_3d_wrt_alignedBrainstemCrop_uv_rawResol_section[:, 2])) == 1
                sec = int(contour_3d_wrt_alignedBrainstemCrop_uv_rawResol_section[0, 2])

                if use_unsided_name_as_key:
                    name = convert_to_unsided_label(name_s)
                else:
                    name = name_s

                structure_contours_wrt_alignedBrainstemCrop_rawResol[sec][name][
                    one_level] = contour_3d_wrt_alignedBrainstemCrop_uv_rawResol_section[..., :2]

    return structure_contours_wrt_alignedBrainstemCrop_rawResol




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Generate images with aligned atlas structures overlaid.')
    parser.add_argument('--stack', help='Enter the animal', required=True)

    #parser.add_argument("image_version", type=str, help="Image version")
    #parser.add_argument("per_structure_alignment_spec", type=str, help="per_structure_alignment_spec, json")
    #parser.add_argument("-g", "--global_alignment_spec", type=str, help="global_alignment_spec, json")
    # parser.add_argument("--structure_list", type=str, help="Json-encoded list of structures (unsided) (Default: all known structures)")
    args = parser.parse_args()

    #image_version = args.image_version
    #per_structure_alignment_spec = load_json(args.per_structure_alignment_spec)
    #simpleGlobal_alignment_spec = load_json(args.global_alignment_spec)

    #structure_list = list(per_structure_alignment_spec.keys())
    stack = args.stack
    #structure_list = ['Amb', 'SNR', '7N', '5N', '7n', 'LRt', 'Sp5C', 'SNC', 'VLL', 'SC', 'IC']
    structure_list = ['SC', 'IC']
    section_margin_um = 1000.
    section_margin = int(section_margin_um / SECTION_THICKNESS)
    valid_secmin = 1
    valid_secmax = 999
    structure_alignemnt_filepath = os.path.join(os.getcwd(), f'{stack}_visualization_per_structure_alignment_spec.json')
    with open(structure_alignemnt_filepath, 'r') as json_file:
        per_structure_alignment_spec = json.load(json_file)
    global_alignment_filepath = os.path.join(os.getcwd(), f'{stack}_visualization_global_alignment_spec.json')
    with open(global_alignment_filepath, 'r') as json_file:
        simpleGlobal_alignment_spec = json.load(json_file)

    auto_contours_all_sec_all_structures_all_levels = defaultdict(lambda: defaultdict(dict))
    simple_global_contours_all_sec_all_structures_all_levels = defaultdict(lambda: defaultdict(dict))
    ########################

    for structure_m in structure_list:

        ####################################################

        local_alignment_spec = per_structure_alignment_spec[structure_m]

        vo = load_transformed_volume_v2(alignment_spec=local_alignment_spec,
                                        return_origin_instead_of_bbox=True,
                                        structure=structure_m)

        # prep2 because at end of get_structure_contours_from_structure_volumes_v2 we used wholebrainXYcropped
        registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners = \
            load_json(os.path.join(REGISTRATION_PARAMETERS_ROOTDIR, 'CSHL_simple_global_registration',
                                   stack + '_registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners.json'))

        (_, _, secmin), (_, _, secmax) = registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[
            structure_m]

        atlas_structures_wrt_wholebrainWithMargin_sections = \
            list(range(max(secmin - section_margin, valid_secmin), min(secmax + 1 + section_margin, valid_secmax)))

        levels = [0.1, 0.25, 0.5, 0.75, 0.99]

        auto_contours_all_sections_one_structure_all_levels = \
            get_structure_contours_from_structure_volumes_v3(volumes={structure_m: vo}, stack=stack,
                                                             sections=atlas_structures_wrt_wholebrainWithMargin_sections,
                                                             resolution='10.0um', level=levels, sample_every=5)

        for sec, contours_one_structure_all_levels in sorted(
                auto_contours_all_sections_one_structure_all_levels.items()):
            for name_s, cnt_all_levels in list(contours_one_structure_all_levels.items()):
                for level, cnt in cnt_all_levels.items():
                    auto_contours_all_sec_all_structures_all_levels[sec][name_s][level] = cnt.astype(np.int)

        ####################################################

        simpleGlobal_vo = load_transformed_volume_v2(alignment_spec=simpleGlobal_alignment_spec,
                                                     return_origin_instead_of_bbox=True,
                                                     structure=structure_m)

        simpleGlobal_contours_all_sections_one_structure_all_levels = \
            get_structure_contours_from_structure_volumes_v3(volumes={structure_m: simpleGlobal_vo}, stack=stack,
                                                             sections=atlas_structures_wrt_wholebrainWithMargin_sections,
                                                             resolution='10.0um', level=levels, sample_every=5)

        for sec, contours_one_structure_all_levels in sorted(
                simpleGlobal_contours_all_sections_one_structure_all_levels.items()):
            for name_s, cnt_all_levels in list(contours_one_structure_all_levels.items()):
                for level, cnt in cnt_all_levels.items():
                    simple_global_contours_all_sec_all_structures_all_levels[sec][name_s][level] = cnt.astype(np.int)

        ####################################

    #         chat_vo = chat_structures[structure_m]

    #         chat_contours_all_sections_all_structures_all_levels = \
    #         get_structure_contours_from_structure_volumes_v3(volumes={structure_m: chat_vo}, stack=stack,
    #                                                          sections=atlas_structures_wrt_wholebrainWithMargin_sections,
    #                                                         resolution='10.0um', level=[.5], sample_every=1)

    #######################################

    for sec in sorted(auto_contours_all_sec_all_structures_all_levels.keys()):

        #    for version in ['NtbNormalizedAdaptiveInvertedGammaJpeg']:
        try:
            # img = load_image_v2(stack=stack, prep_id=2, resol='raw', version=version, section=sec)
            fileLocationManager = FileLocationManager(stack)
            INPUT = os.listdir(os.path.join(fileLocationManager.prep, 'CH1', 'thumbnail_aligned'))

            section_path = os.path.join(INPUT, sec)
            img = io.imread(section_path)
            viz = gray2rgb(img)

            # Draw the locally aligned structure contours in COLOR
            for name_s, cnt_all_levels in auto_contours_all_sec_all_structures_all_levels[sec].items():

                for level, cnt in cnt_all_levels.items():
                    cv2.polylines(viz, [cnt.astype(np.int)], isClosed=True,
                                  color=LEVEL_TO_COLOR_LINE[level], thickness=10)

            # Draw the simple globally aligned structure contours in WHITE
            for name_s, cnt_all_levels in simple_global_contours_all_sec_all_structures_all_levels[sec].items():

                for level, cnt in cnt_all_levels.items():
                    cv2.polylines(viz, [cnt.astype(np.int)], isClosed=True,
                                  color=(255, 255, 255),
                                  thickness=10)

            # #             # Add CHAT contour
            #             if sec in chat_contours_all_sections_all_structures_all_levels:
            #                 chat_cnt = chat_contours_all_sections_all_structures_all_levels[sec][name_s][.5]
            #                 cv2.polylines(viz, [chat_cnt.astype(np.int)], isClosed=True, color=(255,255,255), thickness=20)

            #             fp = os.path.join('/home/yuncong/' + stack + '_atlas_aligned_multilevel_all_structures', version, stack + '_' + version + '_' + ('%03d' % sec) + '.jpg')
            #             print fp
            #             create_parent_dir_if_not_exists(fp)
            #             imsave(fp, viz)

            filepath = os.path.join('/net/birdstore/Active_Atlas_Data/data_root', 'CSHL_registration_visualization',
                                    stack, 'atlas_aligned_structures', ('%03d' % sec) + '.jpg')
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            io.imsave(filepath, viz[::16, ::16])
        #           upload_to_s3(fp)

        except:
            pass

