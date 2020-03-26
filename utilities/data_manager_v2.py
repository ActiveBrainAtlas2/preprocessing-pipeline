import os, sys
import json
import numpy as np
import pandas as pd
import bloscpack as bp
from skimage.io import imread
from metadata import ROOT_DIR, prep_str_to_id_2d
from utilities2015 import load_ini, load_hdf_v2, one_liner_to_arr

class DataManager(object):

    def __init__(self):
        """ setup the attributes for the data manager
        """
        self.metadata_cache = self.generate_metadata_cache()

    def generate_metadata_cache(self):

        all_stacks = os.listdir(ROOT_DIR)

        global metadata_cache
        metadata_cache['image_shape'] = {}
        metadata_cache['anchor_fn'] = {}
        metadata_cache['sections_to_filenames'] = {}
        metadata_cache['filenames_to_sections'] = {}
        metadata_cache['section_limits'] = {}
        metadata_cache['cropbox'] = {}
        metadata_cache['valid_sections'] = {}
        metadata_cache['valid_filenames'] = {}
        metadata_cache['valid_sections_all'] = {}
        metadata_cache['valid_filenames_all'] = {}
        for stack in all_stacks:

            # Don't print out long error messages if base folder not found
            if not os.path.exists(DataManager.get_images_root_folder(stack)):
                # sys.stderr.write("Folder for stack %s not found, skipping.\n" % (stack))
                continue
            # Try to load metadata_cache.json file before doing anything else
            try:
                with open(ROOT_DIR + 'CSHL_data_processed/' + stack + '/' + stack + '_metadata_cache.json') as json_file:
                    saved_metadata = json.load(json_file)
                for key in saved_metadata.keys():
                    # The metadata_cache json file has extraneous keys. (currently only "stack")
                    if key == 'stack':
                        continue
                    if key == 'sections_to_filenames':
                        metadata_cache[key][stack] = {int(k): v for k, v in saved_metadata[key].items()}
                    else:
                        metadata_cache[key][stack] = saved_metadata[key]
                print('Loaded data from saved metadata_cache for ' + stack)
                continue
            except:
                pass

            try:
                metadata_cache['anchor_fn'][stack] = DataManager.load_anchor_filename(stack)
            except Exception as e:
                # sys.stderr.write("Failed to cache %s anchor: %s\n" % (stack, e.message))
                pass

            try:
                metadata_cache['sections_to_filenames'][stack] = DataManager.load_sorted_filenames(stack)[1]
            except Exception as e:
                # sys.stderr.write("Failed to cache %s sections_to_filenames: %s\n" % (stack, e.message))
                pass

            try:
                metadata_cache['filenames_to_sections'][stack] = DataManager.load_sorted_filenames(stack)[0]
                if 'Placeholder' in metadata_cache['filenames_to_sections'][stack]:
                    metadata_cache['filenames_to_sections'][stack].pop('Placeholder')
                if 'Nonexisting' in metadata_cache['filenames_to_sections'][stack]:
                    metadata_cache['filenames_to_sections'][stack].pop('Nonexisting')
                if 'Rescan' in metadata_cache['filenames_to_sections'][stack]:
                    metadata_cache['filenames_to_sections'][stack].pop('Rescan')
            except Exception as e:
                # sys.stderr.write("Failed to cache %s filenames_to_sections: %s\n" % (stack, e.message))
                pass

            try:
                metadata_cache['section_limits'][stack] = DataManager.load_section_limits_v2(stack, prep_id=2)
            except Exception as e:
                # sys.stderr.write("Failed to cache %s section_limits: %s\n" % (stack, e.message))
                pass

            try:
                # alignedBrainstemCrop cropping box relative to alignedpadded
                metadata_cache['cropbox'][stack] = DataManager.load_cropbox_v2(stack, prep_id=2)
            except Exception as e:
                # sys.stderr.write("Failed to cache %s cropbox: %s\n" % (stack, e.message))
                pass

            try:
                first_sec, last_sec = metadata_cache['section_limits'][stack]
                metadata_cache['valid_sections'][stack] = [sec for sec in range(first_sec, last_sec + 1) \
                                                           if sec in metadata_cache['sections_to_filenames'][stack] and \
                                                           not is_invalid(stack=stack, sec=sec)]
                metadata_cache['valid_filenames'][stack] = [metadata_cache['sections_to_filenames'][stack][sec] for sec
                                                            in
                                                            metadata_cache['valid_sections'][stack]]
            except Exception as e:
                # sys.stderr.write("Failed to cache %s valid_sections/filenames: %s\n" % (stack, e.message))
                pass

            try:
                metadata_cache['valid_sections_all'][stack] = [sec for sec, fn in
                                                               metadata_cache['sections_to_filenames'][
                                                                   stack].iteritems() if not is_invalid(fn=fn)]
                metadata_cache['valid_filenames_all'][stack] = [fn for sec, fn in
                                                                metadata_cache['sections_to_filenames'][
                                                                    stack].iteritems() if not is_invalid(fn=fn)]
            except:
                pass

            try:
                metadata_cache['image_shape'][stack] = DataManager.get_image_dimension(stack)
            except Exception as e:
                # sys.stderr.write("Failed to cache %s image_shape: %s\n" % (stack, e.message))
                pass

        return metadata_cache

    @staticmethod
    def get_brain_info_root_folder(stack):
        return os.path.join(ROOT_DIR, stack, 'brains_info')

    @staticmethod
    def get_brain_info_metadata_fp(stack):
        return os.path.join(ROOT_DIR, stack, 'brains_info', 'metadata.ini')

    @staticmethod
    def get_brain_info_progress_fp(stack):
        return os.path.join(ROOT_DIR, stack, 'brains_info', 'progress.ini')


    @staticmethod
    def get_brain_info_progress(stack):
        fp = DataManager.get_brain_info_progress_fp(stack)
        print('test fp ', fp)
        contents_dict = load_ini( fp )
        if contents_dict is None:
            sys.stderr.write( 'No brain_info_progress' )
            return None
        else:
            return contents_dict

    @staticmethod
    def load_sorted_filenames(stack=None, fp=None, redownload=False):
        """
        Get the mapping between section index and image filename.

        Returns:
            filename_to_section, section_to_filename
        """

        if fp is None:
            assert stack is not None, 'Must specify stack'
            fp = DataManager.get_sorted_filenames_filename(stack=stack)

        # download_from_s3(fp, local_root=THUMBNAIL_DATA_ROOTDIR, redownload=redownload)
        filename_to_section, section_to_filename = DataManager.load_data(fp, filetype='file_section_map')
        if 'Placeholder' in filename_to_section:
            filename_to_section.pop('Placeholder')
        return filename_to_section, section_to_filename


    @staticmethod
    def load_data(filepath, filetype=None):

        if not os.path.exists(filepath):
            sys.stderr.write('File does not exist: %s\n' % filepath)

        if filetype == 'bp':
            return bp.unpack_ndarray_file(filepath)
        elif filetype == 'npy':
            return np.load(filepath)
        elif filetype == 'image':
            return imread(filepath)
        elif filetype == 'hdf':
            try:
                return pd.load_hdf(filepath)
            except:
                return load_hdf_v2(filepath)
        elif filetype == 'bbox':
            return np.loadtxt(filepath).astype(np.int)
        elif filetype == 'annotation_hdf':
            contour_df = pd.read_hdf(filepath, 'contours')
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
                xdim_m, ydim_m, zdim_m  = one_liner_to_arr(lines[2], int)
                centroid_f = one_liner_to_arr(lines[3], float)
                xdim_f, ydim_f, zdim_f  = one_liner_to_arr(lines[4], int)

            return global_params, centroid_m, centroid_f, xdim_m, ydim_m, zdim_m, xdim_f, ydim_f, zdim_f
        elif filepath.endswith('ini'):
            fp = "WTF" # EOD, 3/25/2020 i have no idea what fp is supposed to be set to
            return load_ini(fp)
        else:
            sys.stderr.write('File type %s not recognized.\n' % filetype)


    @staticmethod
    def get_sorted_filenames_filename(stack):
        fn = os.path.join( DataManager.get_images_root_folder(stack), stack + '_sorted_filenames.txt')
        return fn

    @staticmethod
    def get_image_filepath(stack, prep_id, version=None, resol=None,
                           section=None, fn=None, ext=None, sorted_filenames_fp=None):
        """
        Args:
            version (str): the version string.

        Returns:
            Absolute path of the image file.
        """
        data_dir = os.path.join(ROOT_DIR, prep_id, 'tif')
        thumbnail_data_dir = os.path.join(ROOT_DIR, prep_id, 'thumbnail')
        if section is not None:
            try:
                metadata_cache['sections_to_filenames'][stack]
            except:
                sys.stderr.write( 'No sorted filenames could be loaded for '+stack+'. May not have been set up correctly.' )
                return


            if sorted_filenames_fp is not None:
                _, sections_to_filenames = DataManager.load_sorted_filenames(fp=sorted_filenames_fp)
                if section not in sections_to_filenames:
                    raise Exception('Section %d is not specified in sorted list.' % section)
                fn = sections_to_filenames[section]
            else:
                if section not in metadata_cache['sections_to_filenames'][stack]:
                    raise Exception('Section %d is not specified in sorted list.' % section)
                fn = metadata_cache['sections_to_filenames'][stack][section]

            if is_invalid(fn=fn, stack=stack):
                raise Exception('Section is invalid: %s.' % fn)
        else:
            assert fn is not None


        if prep_id is not None and (isinstance(prep_id, str) or isinstance(prep_id, str)):
            if prep_id == 'None':
                prep_id = None
            else:
                prep_id = prep_str_to_id_2d[prep_id]

        image_dir = DataManager.get_image_dir_v2(stack=stack, prep_id=prep_id, resol=resol, version=version, data_dir=data_dir, thumbnail_data_dir=thumbnail_data_dir)

        if version is None:
            image_name = fn + ('_prep%d' % prep_id if prep_id is not None else '') + '_%s' % resol + '.' + 'tif'
        else:
            if ext is None:
                if version == 'mask':
                    ext = 'png'
                elif version == 'contrastStretched' or version.endswith('Jpeg') or version == 'jpeg':
                    ext = 'jpg'
                else:
                    ext = 'tif'
            image_name = fn + ('_prep%d' % prep_id if prep_id is not None else '') + '_' + resol + '_' + version + '.' + ext

        image_path = os.path.join(image_dir, image_name)
        return image_path


    ######################################################################################################################
    #                                     ROOT FOLDERS                                                                   #
    ######################################################################################################################

    @staticmethod
    def get_images_root_folder(stack):
        #return os.path.join( os.environ['ROOT_DIR'], stack, 'preprocessing_data' )
        return os.path.join( ROOT_DIR, stack, 'tif')

    @staticmethod
    def get_image_dir(stack, prep_id=None, version=None, resol=None):
        """
        Args:
            version (str): version string
            data_dir: This by default is DATA_DIR, but one can change this ad-hoc when calling the function

        Returns:
            Absolute path of the image directory.
        """
        data_dir = ROOT_DIR


        if prep_id is not None and (isinstance(prep_id, str) or isinstance(prep_id, str)):
            prep_id = prep_str_to_id_2d[prep_id]

        if version is None:
            if resol == 'thumbnail' or resol == 'down64':
                image_dir = os.path.join( DataManager.get_images_root_folder(stack),
                                         stack + ('_prep%d' % prep_id if prep_id is not None else '') + '_%s' % resol)
            else:
                image_dir = os.path.join( DataManager.get_images_root_folder(stack),
                                         stack + ('_prep%d' % prep_id if prep_id is not None else '') + '_%s' % resol)
        else:
            if resol == 'thumbnail' or resol == 'down64':
                image_dir = os.path.join( DataManager.get_images_root_folder(stack),
                                         stack + ('_prep%d' % prep_id if prep_id is not None else '') + '_%s' % resol + '_' + version)
            else:
                image_dir = os.path.join( DataManager.get_images_root_folder(stack),
                                         stack + ('_prep%d' % prep_id if prep_id is not None else '') + '_%s' % resol + '_' + version)

        return image_dir



def is_invalid(fn=None, sec=None, stack=None):
    """
    Determine if a section is invalid (i.e. tagged nonexisting, rescan or placeholder in the brain labeling GUI).
    """
    if sec is not None:
        assert stack is not None, 'is_invalid: if section is given, stack must not be None.'
        if sec not in metadata_cache['sections_to_filenames'][stack]:
            return True
        fn = metadata_cache['sections_to_filenames'][stack][sec]
    else:
        assert fn is not None, 'If sec is not provided, must provide fn'
    return fn in ['Nonexisting', 'Rescan', 'Placeholder']
