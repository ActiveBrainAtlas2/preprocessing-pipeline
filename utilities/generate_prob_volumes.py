import os
import argparse
import sys
import time
from collections import defaultdict

import numpy as np

from utilities.data_manager_v2 import DataManager
from utilities.learning_utilities import load_mxnet_model
from utilities.metadata import all_known_structures, detector_settings, DATA_ROOTDIR, structures_sided_sorted_by_size, \
    SECTION_THICKNESS, singular_structures, convert_to_left_name, convert_to_right_name
from utilities.utilities2015 import load_json, load_ini, save_data, rescale_by_resampling

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='')

parser.add_argument("brain_name", type=str, help="Brain name")
parser.add_argument("detector_id", type=int, help="Detector id")
parser.add_argument("bg_img_version", type=str, help="Version of scoremap visualization background image")
parser.add_argument("-s", "--structure_list", type=str, help="Json-encoded list of structures (unsided) (Default: all known structures)")
args = parser.parse_args()

stack = args.brain_name
detector_id = args.detector_id
bg_img_version = args.bg_img_version

import json
if hasattr(args, 'structure_list') and args.structure_list is not None:
    try:
        structure_list = json.loads(args.structure_list)
    except:
        structure_list = args.structure_list
else:
    structure_list = all_known_structures
    # structure_list = ['Amb', 'SNR', '7N', '5N', '7n', 'LRt', 'Sp5C', 'SNC', 'VLL', 'SC', 'IC']
    print(structure_list)

atlas_spec = dict(name='atlasV7',
                  vol_type='score',
                  resolution='10.0um')


atlas_structures_wrt_canonicalAtlasSpace_atlasResol = \
DataManager.load_original_volume_all_known_structures_v3(atlas_spec, in_bbox_wrt='canonicalAtlasSpace',
                                                        out_bbox_wrt='canonicalAtlasSpace')
# atlas_structures_wrt_canonicalAtlasSpace_atlasResol is an array with two elements
# atlas_structures_wrt_canonicalAtlasSpace_atlasResol[0] is the probability volumes loaded from the atlas
# atlas_structures_wrt_canonicalAtlasSpace_atlasResol[1] is the X Y Z offset 

# For computing score maps.

batch_size = 256
model_dir_name = 'inception-bn-blue'
model_name = 'inception-bn-blue'
# Loading mxnet model causes warnings!
model, mean_img = load_mxnet_model( model_dir_name = model_dir_name, 
                                    model_name = model_name,
                                    num_gpus = 1, 
                                    batch_size = batch_size)
print('\n\n\n\n')
# Loading mxnet model causes warnings!

# Load windowing settings and classifier

# detector_id = 19 # For CSHL nissl data. e.g. MD589, denser window
detector_setting = detector_settings.loc[detector_id]
clfs = DataManager.load_classifiers(classifier_id=detector_setting['feature_classifier_id'])
win_id = detector_setting['windowing_id']

# Define output resolution ('10.0um' is the standard) 

output_resolution = '10.0um'
out_resolution_um = DataManager.sqlController.convert_resolution_string_to_um(resolution=output_resolution, stack=stack)

valid_secmin = np.min(DataManager.metadata_cache['valid_sections'][stack])
valid_secmax = np.max(DataManager.metadata_cache['valid_sections'][stack])

# This should be changed to be in a stack-specific folder
simple_global_bbox_fp = os.path.join(DATA_ROOTDIR, 'CSHL_simple_global_registration',
        stack + '_registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners.json')

# Try to load the XY cropping boxes for each structure, generated from Global Alignment
try:
    registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners = load_json( simple_global_bbox_fp )
    print('Global Alignment files loaded!')
# Make cropping box cover the entire image if Global Alignment was not run
except:
    print('Global Alignment files not found, not using a cropping box')
    
    registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners = {}
    all_structures_total = structures_sided_sorted_by_size
    
    op_path = os.path.join( DATA_ROOTDIR,'CSHL_data_processed',stack, 'operation_configs', 'from_padded_to_brainstem.ini')
    op = load_ini(op_path)
    
    img_x_len = 32*(op['caudal_limit'] - op['rostral_limit'])
    img_y_len = 32*(op['ventral_limit'] - op['dorsal_limit'])
    num_images = 1 + valid_secmax - valid_secmin
    
    for structure in all_structures_total:
        registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[structure] = [[0, 0, 0], [img_x_len, img_y_len, num_images]]
        
######## Identify ROI based on simple global alignment ########
print('\n\nIdentifying ROIs based on simple global alignment:')
print('____________________________________________________\n')

registered_atlas_structures_wrt_wholebrainXYcropped_bboxes_perSection = defaultdict(dict)

section_margin_um = 400.
section_margin = int(section_margin_um / SECTION_THICKNESS)

image_margin_um = 2000.
image_margin = int(np.round(image_margin_um / DataManager.sqlController.convert_resolution_string_to_um('raw', stack)))

# This for loop populates `registered_atlas_structures_wrt_wholebrainXYcropped_bboxes_perSection`
for name_u in structure_list:

    # If structure does not have a left + right hemisphere varient
    if name_u in singular_structures:
        print( name_u )
        print( 'Bounding box: '+str(registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[name_u])+'\n' )

        (xmin, ymin, secmin), (xmax, ymax, secmax) = registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[name_u]

        for sec in range(max(secmin - section_margin, valid_secmin), min(secmax + 1 + section_margin, valid_secmax)+1):

            if DataManager.is_invalid(sec=sec, stack=stack):
                print(sec)
                print('INVALID')
                continue
                
            print(sec)
            print (max(xmin - image_margin, 0), xmax + image_margin, max(ymin - image_margin, 0), ymax + image_margin)

            registered_atlas_structures_wrt_wholebrainXYcropped_bboxes_perSection[name_u][sec] = \
            (max(xmin - image_margin, 0),
             xmax + image_margin,
             max(ymin - image_margin, 0),
             ymax + image_margin)
            
    # Structure present on left (_L) and right (_R) hemispheres
    else:

        a = defaultdict(list)

        # Find bbox for the left-hemisphere location of structure
        lname = convert_to_left_name(name_u)
        if lname in registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners:
            print( lname )
            print( 'Bounding box: '+str(registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[lname])+'\n' )
            
            (xmin, ymin, secmin), (xmax, ymax, secmax) = registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[lname]

            for sec in range(max(secmin - section_margin, valid_secmin), min(secmax + 1 + section_margin, valid_secmax) + 1):

                if DataManager.is_invalid(sec=sec, stack=stack):
                    continue

                a[sec].append((max(xmin - image_margin, 0),
             xmax + image_margin,
             max(ymin - image_margin, 0),
             ymax + image_margin))

        # Find bbox for the right-hemisphere location of structure
        rname = convert_to_right_name(name_u)
        if rname in registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners:
            print( rname )
            print( 'Bounding box: '+str(registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[rname])+'\n' )
            
            (xmin, ymin, secmin), (xmax, ymax, secmax) = registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[rname]

            for sec in range(max(secmin - section_margin, valid_secmin), min(secmax + 1 + section_margin, valid_secmax) + 1):

                if DataManager.is_invalid(sec=sec, stack=stack):
                    continue

                a[sec].append((max(xmin - image_margin, 0),
             xmax + image_margin,
             max(ymin - image_margin, 0),
             ymax + image_margin))

        for sec, bboxes in a.iteritems():
            if len(bboxes) == 1:
                registered_atlas_structures_wrt_wholebrainXYcropped_bboxes_perSection[name_u][sec] = bboxes[0]
            else:
                xmin, ymin = np.min(bboxes, axis=0)[[0,2]]
                xmax, ymax = np.max(bboxes, axis=0)[[1,3]]
                registered_atlas_structures_wrt_wholebrainXYcropped_bboxes_perSection[name_u][sec] = (xmin, xmax, ymin, ymax)

######### Generate score maps ###########
print('\n\nGenerating scoremaps:')
print('____________________________________________________\n')


for name_u in structure_list:
    
    print('\n\nBeginning to generate score maps for structure: %s\n' % (name_u))
    
    if registered_atlas_structures_wrt_wholebrainXYcropped_bboxes_perSection[name_u] == {}:
        print('It appears structure %s does not appear on any slices\n')
        continue
    
    for sec, bbox in sorted(registered_atlas_structures_wrt_wholebrainXYcropped_bboxes_perSection[name_u].items()):

        if DataManager.is_invalid(sec=sec, stack=stack):
            continue

        print('Generating score map: %s, section %s' % (name_u, sec))

        try:

            ############# Generate both scoremap and viz #################

            viz_all_landmarks, scoremap_all_landmarks = \
            draw_scoremap(clfs={name_u: clfs[name_u]},
                          bbox=bbox,
                          scheme='none',
                          win_id=win_id, prep_id=2,
                          stack=stack,
                          return_what='both',
                          sec=sec,
                          model=model, model_name=model_name,
                          mean_img=mean_img,
                          batch_size=batch_size,
                          output_patch_size=224,
                          is_nissl=False,
                          out_resolution_um=out_resolution_um,
                          bg_img_version=bg_img_version,
                          image_shape=metadata_cache['image_shape'][stack],
                          return_wholeimage=True)
            # Scoremap data
            sm = scoremap_all_landmarks[name_u]
            # Scoremap visualization
            viz = viz_all_landmarks[name_u]

            # Save scoremaps
            t = time.time()
            scoremap_bp_filepath = \
            DataManager.get_downscaled_scoremap_filepath(stack=stack, 
                                                         section=sec,
                                                         structure=name_u,
                                                         detector_id=detector_id,
                                                         out_resolution_um=out_resolution_um)
            save_data(sm.astype(np.float16), scoremap_bp_filepath, upload_s3=False)
            sys.stderr.write('Save scoremap: %.2f seconds\n' % (time.time() - t))

            # Save scoremap visualizations
            t = time.time()
            viz_filepath = \
            DataManager.get_scoremap_viz_filepath_v2(stack=stack, 
                                                     section=sec,
                                                     structure=name_u,
                                                     detector_id=detector_id,
                                                     out_resolution=output_resolution)
            save_data(viz, viz_filepath, upload_s3=False)
            sys.stderr.write('Save scoremap viz: %.2f seconds\n' % (time.time() - t))

            del viz_all_landmarks, scoremap_all_landmarks

        except Exception as e:
            sys.stderr.write('Scoremap generation FAILED: %s\n' % e)
            continue

# Takes ~2 hours to get to this point

######### Generate score volumes ##########
print('\n\nGenerating score volumes:')
print('____________________________________________________\n')

for name_u in all_known_structures:

    for name_s in [convert_to_left_name(name_u), convert_to_right_name(name_u)]:
        
        print('\n\nBeginning to generate score volumes for structure: %s\n' % (name_s))

        scoremaps = {}


        if name_s not in registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners:
            sys.stderr.write("Score volume ROI derived from simple global alignment does not exist. Skip generating score volume.\n")
            continue

        (xmin, ymin, s1), (xmax, ymax, s2) = registered_atlas_structures_wrt_wholebrainXYcropped_xysecTwoCorners[name_s]

        for sec in range(max(s1 - section_margin, DataManager.metadata_cache['section_limits'][stack][0]),
                         min(s2 + 1 + section_margin, DataManager.metadata_cache['section_limits'][stack][1])+1):

            if DataManager.is_invalid(sec=sec, stack=stack):
                continue

            try:
                scoremap = DataManager.load_downscaled_scoremap(stack=stack, section=sec, structure=name_u,
                                                                prep_id='alignedBrainstemCrop',
                                                              out_resolution_um=out_resolution_um,
                                                                detector_id=detector_id).astype(np.float32)
            except Exception as e:
                sys.stderr.write('%s\n' % e)
                continue

            mask = DataManager.load_image(stack=stack,
                                             section=sec,
                                             prep_id='alignedBrainstemCrop',
                                             resol='thumbnail', 
                                             version='mask')

            mask_outResol = rescale_by_resampling(mask, 
                                                  new_shape=(scoremap.shape[1], scoremap.shape[0]))

            scoremap[~mask_outResol] = 0
            scoremaps[sec] = scoremap

        try:
            t = time.time()
            volume_outVolResol, volume_origin_wrt_wholebrainXYcropped_outVolResol = \
                    images_to_volume_v2(images=scoremaps,
                                        spacing_um=20.,
                                        in_resol_um=out_resolution_um,
                                        out_resol_um=out_resolution_um)
            sys.stderr.write('Images to volume: %.2f seconds\n' % (time.time() - t))
        except IndexError:
            sys.stderr.write('Generating score volume failed for %s. No sections within bounding box.\n' % name_s)
            continue
        except AssertionError as e:
            sys.stderr.write('Generating score volume failed for %s. %s\n' % (name_s, e))
            continue

        brain_spec = dict(name=stack,
                       vol_type='score',
                       detector_id=detector_id,
                       resolution=output_resolution)

        # Save volume and origin.

        t = time.time()
        save_data(volume_outVolResol.astype(np.float16), \
                  DataManager.get_original_volume_filepath_v2(stack_spec=brain_spec, structure=name_s))

        wholebrainXYcropped_origin_wrt_wholebrain_outVolResol = \
        DataManager.get_domain_origin(stack=stack, 
                                      domain='wholebrainXYcropped',
                                      resolution=output_resolution)
        volume_origin_wrt_wholebrain_outVolResol =\
            volume_origin_wrt_wholebrainXYcropped_outVolResol + wholebrainXYcropped_origin_wrt_wholebrain_outVolResol

        save_data(volume_origin_wrt_wholebrain_outVolResol,
                  DataManager.get_original_volume_origin_filepath_v3(stack_spec=brain_spec, 
                                                                     structure=name_s, 
                                                                     wrt='wholebrain'))
        sys.stderr.write('Save score volume: %.2f seconds\n' % (time.time() - t))

        # Compute gradients.

        t = time.time()
        gradients = compute_gradient_v2((volume_outVolResol,
                                         volume_origin_wrt_wholebrain_outVolResol),
                                         smooth_first=True)
        sys.stderr.write('Compute gradient: %.2f seconds\n' % (time.time() - t))

        t = time.time()
        DataManager.save_volume_gradients(gradients, 
                                          stack_spec=brain_spec, 
                                          structure=name_s)
        sys.stderr.write('Save gradient: %.2f seconds\n' % (time.time() - t))
