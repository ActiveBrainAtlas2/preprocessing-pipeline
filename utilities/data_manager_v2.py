import os, sys
import json
import numpy as np
import pandas as pd
import bloscpack as bp
from skimage.io import imread
from metadata import ROOT_DIR
from utilities2015 import load_ini, load_hdf_v2, one_liner_to_arr

class DataManager(object):

    metadata_cache = {}

    def __init__(self):
        """ setup the attributes for the data manager
        """
        self.metadata_cache = self.generate_metadata_cache()

    def generate_metadata_cache(self):

        all_stacks = os.listdir(ROOT_DIR)

        self.metadata_cache['image_shape'] = {}
        self.metadata_cache['anchor_fn'] = {}
        self.metadata_cache['sections_to_filenames'] = {}
        self.metadata_cache['filenames_to_sections'] = {}
        self.metadata_cache['section_limits'] = {}
        self.metadata_cache['cropbox'] = {}
        self.metadata_cache['valid_sections'] = {}
        self.metadata_cache['valid_filenames'] = {}
        self.metadata_cache['valid_sections_all'] = {}
        self.metadata_cache['valid_filenames_all'] = {}
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
                        self.metadata_cache[key][stack] = {int(k): v for k, v in saved_metadata[key].items()}
                    else:
                        self.metadata_cache[key][stack] = saved_metadata[key]
                print('Loaded data from saved metadata_cache for ' + stack)
                continue
            except:
                pass

            try:
                self.metadata_cache['anchor_fn'][stack] = DataManager.load_anchor_filename(stack)
            except Exception as e:
                # sys.stderr.write("Failed to cache %s anchor: %s\n" % (stack, e.message))
                pass

            try:
                self.metadata_cache['sections_to_filenames'][stack] = DataManager.load_sorted_filenames(stack)[1]
            except Exception as e:
                # sys.stderr.write("Failed to cache %s sections_to_filenames: %s\n" % (stack, e.message))
                pass

            try:
                self.metadata_cache['filenames_to_sections'][stack] = DataManager.load_sorted_filenames(stack)[0]
                if 'Placeholder' in self.metadata_cache['filenames_to_sections'][stack]:
                    self.metadata_cache['filenames_to_sections'][stack].pop('Placeholder')
                if 'Nonexisting' in self.metadata_cache['filenames_to_sections'][stack]:
                    self.metadata_cache['filenames_to_sections'][stack].pop('Nonexisting')
                if 'Rescan' in self.metadata_cache['filenames_to_sections'][stack]:
                    self.metadata_cache['filenames_to_sections'][stack].pop('Rescan')
            except Exception as e:
                # sys.stderr.write("Failed to cache %s filenames_to_sections: %s\n" % (stack, e.message))
                pass

            try:
                self.metadata_cache['section_limits'][stack] = DataManager.load_section_limits_v2(stack, prep_id=2)
            except Exception as e:
                # sys.stderr.write("Failed to cache %s section_limits: %s\n" % (stack, e.message))
                pass

            try:
                # alignedBrainstemCrop cropping box relative to alignedpadded
                self.metadata_cache['cropbox'][stack] = DataManager.load_cropbox_v2(stack, prep_id=2)
            except Exception as e:
                # sys.stderr.write("Failed to cache %s cropbox: %s\n" % (stack, e.message))
                pass

            try:
                first_sec, last_sec = self.metadata_cache['section_limits'][stack]
                self.metadata_cache['valid_sections'][stack] = [sec for sec in range(first_sec, last_sec + 1) \
                                                           if sec in self.metadata_cache['sections_to_filenames'][stack] and \
                                                           not self.is_invalid(stack=stack, sec=sec)]
                self.metadata_cache['valid_filenames'][stack] = [self.metadata_cache['sections_to_filenames'][stack][sec] for sec
                                                            in
                                                            self.metadata_cache['valid_sections'][stack]]
            except Exception as e:
                # sys.stderr.write("Failed to cache %s valid_sections/filenames: %s\n" % (stack, e.message))
                pass

            try:
                self.metadata_cache['valid_sections_all'][stack] = [sec for sec, fn in
                                                               self.metadata_cache['sections_to_filenames'][
                                                                   stack].iteritems() if not self.is_invalid(fn=fn)]
                self.metadata_cache['valid_filenames_all'][stack] = [fn for sec, fn in
                                                                self.metadata_cache['sections_to_filenames'][
                                                                    stack].iteritems() if not self.is_invalid(fn=fn)]
            except:
                pass

            try:
                self.metadata_cache['image_shape'][stack] = DataManager.get_image_dimension(stack)
            except Exception as e:
                # sys.stderr.write("Failed to cache %s image_shape: %s\n" % (stack, e.message))
                pass

        return self.metadata_cache

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
        fn = os.path.join( ROOT_DIR, stack, 'brains_info', 'sorted_filenames.txt')
        return fn


    @staticmethod
    def get_image_filepath(prep_id, version=None, resol=None,
                           section=None, fn=None, ext=None, sorted_filenames_fp=None):
        """
        Args:
            version (str): the version string.

        Returns:
            Absolute path of the image file.
        """
        print('prep_id is ', prep_id, type(prep_id))
        data_dir = os.path.join(ROOT_DIR, prep_id, 'tif')
        thumbnail_data_dir = os.path.join(ROOT_DIR, prep_id, 'thumbnail')
        if section is not None:
            try:
                DataManager.metadata_cache['sections_to_filenames'][prep_id]
            except:
                sys.stderr.write( 'No sorted filenames could be loaded for '+prep_id+'. May not have been set up correctly.' )
                return



            if sorted_filenames_fp is not None:
                _, sections_to_filenames = DataManager.load_sorted_filenames(fp=sorted_filenames_fp)
                if section not in sections_to_filenames:
                    raise Exception('Section %d is not specified in sorted list.' % section)
                fn = sections_to_filenames[section]
            else:
                if section not in DataManager.metadata_cache['sections_to_filenames'][prep_id]:
                    raise Exception('Section %d is not specified in sorted list.' % section)
                fn = DataManager.metadata_cache['sections_to_filenames'][prep_id][section]

            if DataManager.is_invalid(fn=fn, stack=prep_id):
                raise Exception('Section is invalid: %s.' % fn)
        else:
            assert fn is not None

        image_dir = DataManager.get_image_dir(prep_id=prep_id, resol=resol, version=version)
        image_dir = os.path.join(ROOT_DIR, prep_id, 'raw')
        if version is None:
            image_name = '{}_{}_{}.tif'.format(fn, prep_id, resol)
        else:
            if ext is None:
                if version == 'mask':
                    ext = 'png'
                elif version == 'contrastStretched' or version.endswith('Jpeg') or version == 'jpeg':
                    ext = 'jpg'
                else:
                    ext = 'tif'
            image_name = '{}_{}_{}_{}.{}'.format(fn, prep_id, resol, version, ext)

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
    def get_image_dir(prep_id, version=None, resol=None):
        """
        Args:
            version (str): version string
        Returns:
            Absolute path of the image directory.
        """
        data_dir = ROOT_DIR
        print('prep_id is ', prep_id, type(prep_id))

        if resol == 'thumbnail' or resol == 'down64':
            image_dir = os.path.join( ROOT_DIR, prep_id, 'thumbnail')
        else:
            image_dir = os.path.join( ROOT_DIR, prep_id, 'tif')

        return image_dir

    @staticmethod
    def setup_get_raw_fp(stack):
        return os.path.join(ROOT_DIR, stack,  'raw' )

    @staticmethod
    def setup_get_thumbnail_fp(stack):
        return os.path.join(ROOT_DIR, stack, 'thumbnail' )

    @staticmethod
    def setup_get_raw_fp_secondary_channel(stack, channel):
        return os.path.join(ROOT_DIR, stack, '{}'.format(channel) )






    def is_invalid(self, fn=None, sec=None, prep_id=None):
        """
        Determine if a section is invalid (i.e. tagged nonexisting, rescan or placeholder in the brain labeling GUI).
        """
        if sec is not None:
            assert prep_id is not None, 'is_invalid: if section is given, prep_id must not be None.'
            if sec not in self.metadata_cache['sections_to_filenames'][prep_id]:
                return True
            fn = self.metadata_cache['sections_to_filenames'][prep_id][sec]
        else:
            assert fn is not None, 'If sec is not provided, must provide fn'
        return fn in ['Nonexisting', 'Rescan', 'Placeholder']
