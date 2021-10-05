import os
import json
import neuroglancer
import numpy as np


#from lib.utilities_contour import create_alignment_specs, load_transformed_volume, load_json, \
#    get_structure_contours_from_structure_volumes_v3, VOL_DIR
from lib.file_location import DATA_PATH
from lib.utilities_atlas import ATLAS
ATLAS_PATH = os.path.join(DATA_PATH, 'atlas_data', ATLAS)


def get_structure_colorsXXX():
    pass
    #color_filepath = os.path.join(PIPELINE_ROOT, 'utilities/neuroglancer/contours/json_cache', 'struct_to_color.json')
    #with open(color_filepath, 'r') as json_file:
    #    structure_to_color = json.load(json_file)
    #return structure_to_color


def get_ng_params(stack):
    # This json file contains a set of neccessary parameters for each stack
    stack_param_file = os.path.join('/home/eddyod/programming/pipeline_utility/contours/json_cache/stack_parameters_ng.json')
    with open(stack_param_file, 'r') as file:
        stack_parameters_ng = json.load(file)
    # Return the parameters of the specified stack
    return stack_parameters_ng[stack]


# Tranforms volume data to contours
def image_contour_generatorXXX(stack, detector_id, structure, use_local_alignment=True, image_prep=2, threshold=0.5):
    pass
    """
    Loads volumes generated from running through the atlas pipeline, transforms them into a set of contours.

    Returns the first and last section spanned from the contours, as well as the contour itself which is stored as a dictionary.
    """
    """
    fn_vis_global, fn_vis_structures = create_alignment_specs(stack, detector_id)

    # Load local transformed volumes
    #         str_alignment_spec = load_json(fn_vis_structures)[structure]
    with open(fn_vis_structures, 'r') as json_file:
        str_alignment_spec = json.load(json_file)[structure]
    vol = load_transformed_volume(str_alignment_spec, structure)

    numpyfile = 'atlasV7_10.0um_scoreVolume_{}.npy'.format(structure)
    #numpyfile = '{}_volume.npy'.format(structure)
    #atlasV7_10.0um_scoreVolume_VLL_R_origin_wrt_canonicalAtlasSpace.txt
    txtfile = 'atlasV7_10.0um_scoreVolume_{}_origin_wrt_canonicalAtlasSpace.txt'.format(structure)
    data_path = os.path.join(DATA_PATH, 'CSHL_volumes/all_brains/atlasV7/atlasV7_10.0um_scoreVolume/score_volumes')
    try:
        t1 = np.load(os.path.join(data_path, numpyfile))
    except:
        print('Could not load:', numpyfile)
    try:
        t2 = np.loadtxt(os.path.join(data_path, txtfile))
    except:
        print('Could not load:', txtfile)
    # vol is a tuple of np array and 3 numbers
    vol = (t1, t2)
    # Load collection of bounding boxes for every structure
    fileLocationManager = FileLocationManager(stack)
    registered_atlas_structure_file = os.path.join(fileLocationManager.brain_info,
                                                   'registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners.json')
    registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners = load_json(registered_atlas_structure_file)
    # Load cropping box for structure. Only need the valid min and max sections though
    (_, _, secmin), (_, _, secmax) = registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[structure]
    # Load range of sections for particular structure
    valid_secmin = 1
    valid_secmax = 999
    section_margin = 50  # 1000um margin / 20um per slice
    atlas_structures_wrt_wholebrainWithMargin_sections = \
        list(range(max(secmin - section_margin, valid_secmin), min(secmax + 1 + section_margin, valid_secmax)))

    print('atlas_structures_wrt_wholebrainWithMargin_sections', atlas_structures_wrt_wholebrainWithMargin_sections)
    # Choose thresholds for probability volumes
    levels = [threshold]

    # LOAD CONTOURS FROM VOLUME
    str_contour = get_structure_contours_from_structure_volumes_v3(volumes={structure: vol}, stack=stack,
                                                                   sections=atlas_structures_wrt_wholebrainWithMargin_sections,
                                                                   resolution='10.0um', level=levels, sample_every=5)
    # Check number sections that the contours are present on
    str_keys = list(str_contour.keys())
    valid_sections = []
    for key in str_keys:
        print('key', key)
        if isinstance(key, int) and key > 1:
            valid_sections.append(key)
            # Need to check individual "levels" are on this section as well.
            #    (0.1 threshold spans more slices than 0.9)
    if len(valid_sections) == 0:
        return None, None, None
    valid_sections.sort()
    num_valid_sections = len(valid_sections)
    first_sec = valid_sections[0]
    last_sec = valid_sections[len(valid_sections) - 1]

    # LOAD prep5->prep2 cropbox
    if image_prep == 5:
        # wholeslice_to_brainstem = -from_padded_to_wholeslice, from_padded_to_brainstem
        ini_fp = os.environ[
                     'ATLAS_DATA_ROOT_DIR'] + 'CSHL_data_processed/' + stack + '/operation_configs/from_padded_to_brainstem.ini'
        with open(ini_fp, 'r') as fn:
            contents_list = fn.read().split('\n')
        for line in contents_list:
            if 'rostral_limit' in line:
                rostral_limit = int(line.split(' ')[2])
            if 'dorsal_limit' in line:
                dorsal_limit = int(line.split(' ')[2])
        ini_fp = os.environ[
                     'ATLAS_DATA_ROOT_DIR'] + 'CSHL_data_processed/' + stack + '/operation_configs/from_padded_to_wholeslice.ini'
        with open(ini_fp, 'r') as fn:
            contents_list = fn.read().split('\n')
        for line in contents_list:
            if 'rostral_limit' in line:
                rostral_limit = rostral_limit - int(line.split(' ')[2])
            if 'dorsal_limit' in line:
                dorsal_limit = dorsal_limit - int(line.split(' ')[2])
        # DONE LOADING PREP5 OFFSETS
    elif image_prep == 2:
        rostral_limit = 0
        dorsal_limit = 0

    # PLOT Contours
    contour_str = str_contour[valid_sections[num_valid_sections // 2]][structure][levels[0]]
    # print('contour_str', contour_str)
    # Downsample
    y_len, x_len = np.shape(contour_str)
    x_list = []
    y_list = []
    for y in range(y_len):
        x_list.append(rostral_limit + contour_str[y][0] / 32)
        y_list.append(dorsal_limit + contour_str[y][1] / 32)

    # PLOT Structure overlayed on thumbnail image
    # sorted_fns = load_sorted_filenames(stack=stack)[0].keys()
    # fp = DataManager.get_image_filepath_v2(stack=stack, prep_id=5, resol='thumbnail', version='gray', fn=sorted_fns[int(len(sorted_fns)/2)])
    # img_fn = metadata_cache['sections_to_filenames'][stack][last_sec-num_valid_sections/2]

    # fp = DataManager.get_image_filepath_v2(stack=stack, prep_id=image_prep, resol='thumbnail', version='gray', fn=img_fn)
    #     img = imread(fp)
    #     plt.imshow( img, cmap='gray' )
    #     plt.scatter(x_list,y_list,s=1, color='r')
    #     plt.show()

    return str_contour, first_sec, last_sec
    """

##### this method does lots of the work
def add_structure_to_neuroglancer(viewer, str_contour, structure, stack, first_sec, last_sec, color_radius=4,
                                  xy_ng_resolution_um=10, threshold=0.5, color=1, solid_volume=False,
                                  no_offset_big_volume=False, save_results=False, return_with_offsets=False,
                                  add_to_ng=True, human_annotation=False):
    """
    Takes in the contours of a structure as well as the name, sections spanned by the structure, and a list of
    parameters that dictate how it is rendered.

    Returns the binary structure volume.
    """
    xy_ng_resolution_um = xy_ng_resolution_um  # X and Y voxel length in microns
    color_radius = color_radius * (10.0 / xy_ng_resolution_um) ** 0.5

    #stack_parameters_ng = get_ng_params(stack)
    #print('stack_parameters_ng', stack_parameters_ng)
    #ng_section_min = stack_parameters_ng['prep2_section_min']
    #ng_section_max = stack_parameters_ng['prep2_section_max']
    #s3_offset_from_local_x = stack_parameters_ng['local_offset_x']
    #s3_offset_from_local_y = stack_parameters_ng['local_offset_y']
    #s3_offset_from_local_slices = stack_parameters_ng['local_offset_slices']

    ng_section_min = 92
    ng_section_max = 370
    s3_offset_from_local_x = 0
    s3_offset_from_local_y = 0

    # Max and Min X/Y Values given random initial values that will be replaced
    # X and Y resolution will be specified by the user in microns (xy_ng_resolution_umx by y_ng_resolution_um)
    max_x = 0
    max_y = 0
    min_x = 9999999
    min_y = 9999999
    # 'min_z' is the relative starting section (if the prep2 sections start at slice 100, and the structure starts at slice 110, min_z is 10 )
    # Z resolution is 20um for simple 1-1 correspondance with section thickness
    max_z = (last_sec - ng_section_min)
    min_z = (first_sec - ng_section_min)
    if max_z > ng_section_max:
        max_z = ng_section_min
    if min_z < 0:
        min_z = 0
    # Scaling factor is (0.46/X). Scaling from resolution of 0.46 microns to X microns.
    scale_xy = 0.46 / xy_ng_resolution_um

    # X,Y are 10um voxels. Z is 20um voxels.
    # str_contour_ng_resolution is the previous contour data rescaled
    # to neuroglancer resolution
    str_contour_ng_resolution = {}
    for section in str_contour:
        # Load (X,Y) coordinates on this contour
        section_contours = str_contour[section][structure][threshold]
        # (X,Y) coordinates will be rescaled to the new resolution and placed here
        # str_contour_ng_resolution starts at z=0 for simplicity, must provide section offset later on
        str_contour_ng_resolution[section - first_sec] = []
        # Number of (X,Y) coordinates
        num_contours = len(section_contours)
        # Cycle through each coordinate pair
        for coordinate_pair in range(num_contours):
            curr_coors = section_contours[coordinate_pair]
            # Rescale coordinate pair and add to new contour dictionary
            str_contour_ng_resolution[section - first_sec].append([scale_xy * curr_coors[0], scale_xy * curr_coors[1]])
            # Replace Min/Max X/Y values with new extremes
            min_x = min(scale_xy * curr_coors[0], min_x)
            min_y = min(scale_xy * curr_coors[1], min_y)
            max_x = max(scale_xy * curr_coors[0], max_x)
            max_y = max(scale_xy * curr_coors[1], max_y)

    # Cast max and min values to int as they are used to build 3D numpy matrix
    max_x = int(np.ceil(max_x))
    max_y = int(np.ceil(max_y))
    min_x = int(np.floor(min_x))
    min_y = int(np.floor(min_y))

    # Create empty 'structure_volume' using min and max values found earlier. Acts as a bounding box for now
    structure_volume = np.zeros((max_z - min_z, max_y - min_y, max_x - min_x), dtype=np.uint8)
    z_voxels, y_voxels, x_voxels = np.shape(structure_volume)
    # print(  np.shape(structure_volume) )

    # Go through every slice. For every slice color in the voxels corrosponding to the contour's coordinate pair
    for slice in range(z_voxels):

        # For Human Annotated files, sometimes there is a missing set of contours for a slice
        try:
            slice_contour = np.asarray(str_contour_ng_resolution[slice])
        except:
            continue

        for xy_pair in slice_contour:
            x_voxel = int(xy_pair[0]) - min_x
            y_voxel = int(xy_pair[1]) - min_y

            structure_volume[slice, y_voxel, x_voxel] = color

            # Instead of coloring a single voxel, color all in a specified radius from this voxel!
            lower_bnd_offset = int(np.floor(1 - color_radius))
            upper_bnd_offset = int(np.ceil(color_radius))
            for x_coor_color_radius in range(lower_bnd_offset, upper_bnd_offset):
                for y_coor_color_radius in range(lower_bnd_offset, upper_bnd_offset):

                    x_displaced_voxel = x_voxel + x_coor_color_radius
                    y_displaced_voxel = y_voxel + y_coor_color_radius
                    distance = ((y_voxel - y_displaced_voxel) ** 2 + (x_voxel - x_displaced_voxel) ** 2) ** 0.5
                    # If the temporary coordinate is within the specified radius AND inside the 3D matrix
                    if distance < color_radius and \
                            x_displaced_voxel < x_voxels and \
                            y_displaced_voxel < y_voxels and \
                            x_displaced_voxel > 0 and \
                            y_displaced_voxel > 0:
                        try:
                            # Set temporary coordinate to be visible
                            structure_volume[slice, y_displaced_voxel, x_displaced_voxel] = color
                        except:
                            pass

        if solid_volume:
            structure_volume[slice, :, :] = fill_in_structure(structure_volume[slice, :, :], color)

    # structure_volume

    display_name = structure + '_' + str(threshold) + '_' + str(color)

    # If the amount of slices to shift by is nonzero
    z_offset = min_z

    # For annoying reasons, it's possible that the croppingbox on S3 is sometimes different than local
    if s3_offset_from_local_x != 0 or s3_offset_from_local_y != 0:
        hc_x_offset = s3_offset_from_local_x * 10 / xy_ng_resolution_um
        hc_y_offset = s3_offset_from_local_y * 10 / xy_ng_resolution_um
        true_ng_x_offset = min_x + hc_x_offset
        true_ng_y_offset = min_y + hc_y_offset
    else:
        true_ng_x_offset = min_x
        true_ng_y_offset = min_y
    xyz_structure_offsets = [true_ng_x_offset, true_ng_y_offset, z_offset]

    # If instead of a small volume and an offset, we want no offset and an extremely large+sparse volume
    if no_offset_big_volume:
        big_sparse_structure_volume = np.zeros(
            (z_voxels + z_offset, y_voxels + true_ng_y_offset, x_voxels + true_ng_x_offset), dtype=np.uint8)

        try:
            big_sparse_structure_volume[-z_voxels:, -y_voxels:, -x_voxels:] = structure_volume
        # If part of the structure ends up being cut off due to cropping, retake the size of it
        except Exception as e:
            str_new_voxels_zyx = np.shape(structure_volume)
            large_sparse_str_voxels_zyx = np.shape(big_sparse_structure_volume)
            low_end_z_len = np.min([large_sparse_str_voxels_zyx[0], str_new_voxels_zyx[0]])
            low_end_y_len = np.min([large_sparse_str_voxels_zyx[1], str_new_voxels_zyx[1]])
            low_end_x_len = np.min([large_sparse_str_voxels_zyx[2], str_new_voxels_zyx[2]])
            print(e)  # Maybe can remove this whole block after new changes
            print('Cutting out some slices on the edge of the structure')
            print('New shape: ', low_end_z_len, low_end_y_len, low_end_x_len)
            big_sparse_structure_volume[-low_end_z_len:, -low_end_y_len:, -low_end_x_len:] = \
                structure_volume[-low_end_z_len:, -low_end_y_len:, -low_end_x_len:]
            # big_sparse_structure_volume[-str_new_voxels_zyx[0]:,-str_new_voxels_zyx[1]:,-str_new_voxels_zyx[2]:] = \
            #    structure_volume[-large_sparse_str_voxels_zyx[0]:,-large_sparse_str_voxels_zyx[1]:,-large_sparse_str_voxels_zyx[2]:]

        # del structure_volume
        structure_volume = big_sparse_structure_volume.copy()
        true_ng_x_offset = 0
        true_ng_y_offset = 0
        min_z = 0
    if add_to_ng:
        dims = neuroglancer.CoordinateSpace(
            names=['x', 'y', 'z'],
            units=['nm', 'nm', 'nm'],
            scales=[10, 10, 10])
        with viewer.txn() as s:
            s.layers[display_name] = neuroglancer.SegmentationLayer(
                source=neuroglancer.LocalVolume(
                    data=structure_volume,  # Z,Y,X
                    dimensions=dims,
                    voxel_offset=[true_ng_x_offset, true_ng_y_offset, min_z]  # X Y Z
                ),
                segments=[color]
            )

    if save_results:
        volumes_have_offset = not no_offset_big_volume
        fp_volume_root = os.path.join(ATLAS_PATH, stack, 'volumes')

        if not os.path.exists(fp_volume_root):
            os.makedirs(fp_volume_root)
            # Save volume
        volume_fp = os.path.join(fp_volume_root, structure + '_volume.npy')
        np.save(volume_fp, structure_volume)

        if volumes_have_offset:
            # Save offsets
            volume_offset_fp = os.path.join(fp_volume_root, structure + '_offset.txt')
            with open(volume_offset_fp, 'w') as offset_file:
                insert_str = str(min_x + hc_x_offset) + " " + str(min_y + hc_y_offset) + " " + str(min_z)
                offset_file.write(insert_str)
            offset_file.close()

    if return_with_offsets:
        return structure_volume, xyz_structure_offsets
    return structure_volume



def create_volumeXXX(str_contour, structure, first_sec, last_sec, color=1):
    """
    Takes in the contours of a structure as well as the name, sections spanned by the structure, and a list of
    parameters that dictate how it is rendered.
    Returns the binary structure volume.
    """
    xy_ng_resolution_um = 10
    color_radius = 3
    xy_ng_resolution_um = xy_ng_resolution_um  # X and Y voxel length in microns
    color_radius = color_radius * (10.0 / xy_ng_resolution_um) ** 0.5
    ng_section_min = 92
    ng_section_max = 370

    # Max and Min X/Y Values given random initial values that will be replaced
    # X and Y resolution will be specified by the user in microns (xy_ng_resolution_umx by y_ng_resolution_um)
    max_x = 0
    max_y = 0
    min_x = 9999999
    min_y = 9999999
    # 'min_z' is the relative starting section (if the prep2 sections start at slice 100, and the structure starts at slice 110, min_z is 10 )
    # Z resolution is 20um for simple 1-1 correspondance with section thickness
    max_z = (last_sec - ng_section_min)
    min_z = (first_sec - ng_section_min)
    if max_z > ng_section_max:
        max_z = ng_section_min
    if min_z < 0:
        min_z = 0
    # Scaling factor is (0.46/X). Scaling from resolution of 0.46 microns to X microns. x is 10um for neuroglancer in x,y space.
    scale_xy = 0.46 / xy_ng_resolution_um

    # X,Y are 10um voxels. Z is 20um voxels.
    # str_contour_ng_resolution is the previous contour data rescaled
    # to neuroglancer resolution
    str_contour_ng_resolution = {}
    for section in str_contour:
        # Load (X,Y) coordinates on this contour
        section_contours = str_contour[section][structure]
        # (X,Y) coordinates will be rescaled to the new resolution and placed here
        # str_contour_ng_resolution starts at z=0 for simplicity, must provide section offset later on
        str_contour_ng_resolution[section - first_sec] = []
        # Number of (X,Y) coordinates
        num_contours = len(section_contours)
        print(section, structure, num_contours)
        continue
        # Cycle through each coordinate pair
        for coordinate_pair in range(num_contours):
            curr_coors = section_contours[coordinate_pair]
            # Rescale coordinate pair and add to new contour dictionary
            x = curr_coors[0]
            y = curr_coors[1]
            str_contour_ng_resolution[section - first_sec].append([scale_xy * x, scale_xy * y])
            # Replace Min/Max X/Y values with new extremes
            min_x = min(scale_xy * x, min_x)
            min_y = min(scale_xy * y, min_y)
            max_x = max(scale_xy * x, max_x)
            max_y = max(scale_xy * y, max_y)
    # return np.zeros((3,3,3)), [1,2,3]
    # Cast max and min values to int as they are used to build 3D numpy matrix
    max_x = int(np.ceil(max_x))
    max_y = int(np.ceil(max_y))
    min_x = int(np.floor(min_x))
    min_y = int(np.floor(min_y))

    # Create empty 'structure_volume' using min and max values found earlier. Acts as a bounding box for now
    structure_volume = np.zeros((max_z - min_z, max_y - min_y, max_x - min_x), dtype=np.uint8)
    z_voxels, y_voxels, x_voxels = np.shape(structure_volume)
    # print(  np.shape(structure_volume) )

    # Go through every slice. For every slice color in the voxels corrosponding to the contour's coordinate pair
    for slice in range(z_voxels):
        # For Human Annotated files, sometimes there is a missing set of contours for a slice
        try:
            slice_contour = np.asarray(str_contour_ng_resolution[slice])
        except:
            continue

        for xy_pair in slice_contour:
            x_voxel = int(xy_pair[0]) - min_x
            y_voxel = int(xy_pair[1]) - min_y

            structure_volume[slice, y_voxel, x_voxel] = color

            # Instead of coloring a single voxel, color all in a specified radius from this voxel!
            lower_bnd_offset = int(np.floor(1 - color_radius))
            upper_bnd_offset = int(np.ceil(color_radius))
            for x_coor_color_radius in range(lower_bnd_offset, upper_bnd_offset):
                for y_coor_color_radius in range(lower_bnd_offset, upper_bnd_offset):

                    x_displaced_voxel = x_voxel + x_coor_color_radius
                    y_displaced_voxel = y_voxel + y_coor_color_radius
                    distance = ((y_voxel - y_displaced_voxel) ** 2 + (x_voxel - x_displaced_voxel) ** 2) ** 0.5
                    # If the temporary coordinate is within the specified radius AND inside the 3D matrix
                    if distance < color_radius and \
                            x_displaced_voxel < x_voxels and \
                            y_displaced_voxel < y_voxels and \
                            x_displaced_voxel > 0 and \
                            y_displaced_voxel > 0:
                        try:
                            # Set temporary coordinate to be visible
                            structure_volume[slice, y_displaced_voxel, x_displaced_voxel] = color
                        except:
                            pass

    return structure_volume, [min_x, min_y, min_z]



def fill_in_structure(voxel_sheet, color):
    contour_coordinates = []
    y_len, x_len = np.shape(voxel_sheet)

    for y in range(y_len):
        for x in range(x_len):
            # If this pixel is colored in
            if not voxel_sheet[y, x] == 0:
                contour_coordinates.append([y, x])

    for y in range(y_len):
        for x in range(x_len):
            has_lr, has_ur, has_ll, has_ul = [False, False, False, False]

            for coordinate in contour_coordinates:
                coor_y = coordinate[0]
                coor_x = coordinate[1]

                if coor_y < y and coor_x < x:
                    has_ll = True
                if coor_y < y and coor_x > x:
                    has_lr = True
                if coor_y > y and coor_x < x:
                    has_ul = True
                if coor_y > y and coor_x > x:
                    has_ur = True

            if has_lr == True and has_ur == True and has_ll == True and has_ul == True:
                voxel_sheet[y, x] = color
    return voxel_sheet


def get_contours_from_annotations(contour_stack, target_structure, hand_annotations, densify=0):
    MD585_ng_section_min = 83
    num_annotations = len(hand_annotations)
    str_contours_annotation = {}
    for i in range(num_annotations):
        structure = hand_annotations['name'][i]
        side = hand_annotations['side'][i]
        section = hand_annotations['section'][i]
        first_sec = 0
        last_sec = 0
        if side == 'R' or side == 'L':
            structure = structure + '_' + side
        if structure == target_structure:
            vertices = hand_annotations['vertices'][i]
            for _ in range(densify):
                vertices = get_dense_coordinates(vertices)
            # Skip sections before the 22nd prep2 section for MD585 as there are clear errors
            if contour_stack == 'MD585XXX' and section < MD585_ng_section_min + 22:
                continue
            str_contours_annotation[section] = {}
            str_contours_annotation[section][structure] = {}
            str_contours_annotation[section][structure] = vertices
    try:
        first_sec = np.min(list(str_contours_annotation.keys()))
        last_sec = np.max(list(str_contours_annotation.keys()))
    except:
        pass
    return str_contours_annotation, first_sec, last_sec


def min_max_sections(target_structure, hand_annotations):
    num_annotations = len(hand_annotations)
    str_contours_annotation = {}

    for i in range(num_annotations):
        side = hand_annotations['side'][i]
        structure = hand_annotations['name'][i]
        section = hand_annotations['section'][i]
        first_sec = 0
        last_sec = 0
        if side == 'R' or side == 'L':
            structure = structure + '_' + side

        if structure.upper() == target_structure.upper():
            vertices = hand_annotations['vertices'][i]
            str_contours_annotation[section] = {}
            str_contours_annotation[section][structure] = {}
            str_contours_annotation[section][structure][1] = vertices

    try:
        first_sec = np.min(list(str_contours_annotation.keys()))
        last_sec = np.max(list(str_contours_annotation.keys()))
    except:
        print('keys:', target_structure, len(str_contours_annotation.keys()), end="\t")


    return first_sec, last_sec


def create_volume(str_contour, structure, color):
    """
    Takes in the contours of a structure as well as the name,
    sections spanned by the structure, and a list of
    parameters that dictate how it is rendered.
    Returns the binary structure volume.
    """
    xy_ng_resolution_um = 5 # X and Y voxel length in microns
    color_radius = 1.5
    ng_section_min = 92
    ng_section_max = 370
    ng_section_min = 0
    ng_section_max = 445
    first_sec = min(str_contour.keys())
    last_sec = max(str_contour.keys())
    print('first and last sec', first_sec, last_sec)
    # Max and Min X/Y Values given random initial values that will be replaced
    # X and Y resolution will be specified by the user in microns (xy_ng_resolution_umx by y_ng_resolution_um)
    max_x = 0
    max_y = 0
    min_x = 9999999
    min_y = 9999999
    # 'min_z' is the relative starting section (if the prep2 sections start at slice 100,
    #  and the structure starts at slice 110, min_z is 10 )
    # Z resolution is 20um for simple 1-1 correspondance with section thickness
    max_z = (last_sec - ng_section_min)
    min_z = (first_sec - ng_section_min)
    if max_z > ng_section_max:
        max_z = ng_section_min
    if min_z < 0:
        min_z = 0
    # orig is 0.46
    # Scaling factor is (0.452/X). Scaling from resolution of 0.452 microns to X microns.
    # x is 10um for neuroglancer in x,y space.
    scale_xy = 0.46 / xy_ng_resolution_um
    scale_xy = 1

    # X,Y are 10um voxels. Z is 20um voxels.
    # str_contour_ng_resolution is the previous contour data rescaled
    # to neuroglancer resolution
    str_contour_ng_resolution = {}
    for section, vertices in str_contour.items():
        # Load (X,Y) coordinates on this contour
        # section_contours = str_contour[section][structure]
        # (X,Y) coordinates will be rescaled to the new resolution and placed here
        # str_contour_ng_resolution starts at z=0 for simplicity, must provide section offset later on
        str_contour_ng_resolution[section - first_sec] = []
        # Number of (X,Y) coordinates
        num_contours = vertices.shape[0]
        # Cycle through each coordinate pair
        for coordinate_pair in range(num_contours):
            curr_coors = vertices[coordinate_pair]
            # Rescale coordinate pair and add to new contour dictionary
            x = curr_coors[0]
            y = curr_coors[1]
            str_contour_ng_resolution[section - first_sec].append([scale_xy * x, scale_xy * y])
            # Replace Min/Max X/Y values with new extremes
            min_x = min(scale_xy * x, min_x)
            min_y = min(scale_xy * y, min_y)
            max_x = max(scale_xy * x, max_x)
            max_y = max(scale_xy * y, max_y)
    # Cast max and min values to int as they are used to build 3D numpy matrix
    max_x = int(np.ceil(max_x))
    max_y = int(np.ceil(max_y))
    min_x = int(np.floor(min_x))
    min_y = int(np.floor(min_y))

    # Create empty 'structure_volume' using min and max values found earlier.
    # Acts as a bounding box for now
    # e.g. Shape of SC for atlasV7 is 176,238,377
    print('x range', min_x, max_x, 'diff', max_x-min_x)
    print('y range', min_y, max_y, 'diff',  max_y-min_y)
    print('z range', min_z, max_z, 'diff',  max_z-min_z)
    structure_volume = np.zeros((max_z - min_z, max_y - min_y, max_x - min_x),
                                dtype=np.uint8)
    z_voxels, y_voxels, x_voxels = np.shape(structure_volume)

    # Go through every slice. For every slice color in the voxels corrosponding to the contour's coordinate pair
    for slice in range(z_voxels):
        # For Human Annotated files, sometimes there is a missing set of contours for a slice
        try:
            slice_contour = np.asarray(str_contour_ng_resolution[slice])
        except:
            continue

        for xy_pair in slice_contour:
            x_voxel = int(xy_pair[0]) - min_x
            y_voxel = int(xy_pair[1]) - min_y

            structure_volume[slice, y_voxel, x_voxel] = color

            # Instead of coloring a single voxel, color all in a specified radius from this voxel!
            lower_bnd_offset = int(np.floor(1 - color_radius))
            upper_bnd_offset = int(np.ceil(color_radius))
            for x_coor_color_radius in range(lower_bnd_offset, upper_bnd_offset):
                for y_coor_color_radius in range(lower_bnd_offset, upper_bnd_offset):

                    x_displaced_voxel = x_voxel + x_coor_color_radius
                    y_displaced_voxel = y_voxel + y_coor_color_radius
                    distance = ((y_voxel - y_displaced_voxel) ** 2 + (x_voxel - x_displaced_voxel) ** 2) ** 0.5
                    # If the temporary coordinate is within the specified radius AND inside the 3D matrix
                    if distance < color_radius and \
                            x_displaced_voxel < x_voxels and \
                            y_displaced_voxel < y_voxels and \
                            x_displaced_voxel > 0 and \
                            y_displaced_voxel > 0:
                        try:
                            # Set temporary coordinate to be visible
                            structure_volume[slice, y_displaced_voxel, x_displaced_voxel] = color
                        except:
                            pass

    return structure_volume, [min_x, min_y, min_z]



def get_dense_coordinates(coor_list):
    dense_coor_list = []
    # Shortest distance, x, y

    # for x, y in coor_list:
    for i in range(len(coor_list) - 1):
        x, y = coor_list[i]
        x_next, y_next = coor_list[i + 1]

        x_mid = (x + x_next) / 2
        y_mid = (y + y_next) / 2

        dense_coor_list.append([x, y])
        dense_coor_list.append([x_mid, y_mid])

        if i == len(coor_list) - 2:
            dense_coor_list.append([x_next, y_next])
            x, y = coor_list[0]
            x_mid = (x + x_next) / 2
            y_mid = (y + y_next) / 2
            dense_coor_list.append([x_mid, y_mid])

    return dense_coor_list
