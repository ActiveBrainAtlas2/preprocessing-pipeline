import os, sys
import numpy as np
import pandas as pd
import bloscpack as bp
from skimage.io import imread
from metadata import ROOT_DIR
from utilities2015 import load_ini, load_hdf_v2, one_liner_to_arr

class DataManager(object):


    @staticmethod
    def get_brain_info_root_folder():
        return os.path.join(ROOT_DIR, 'brains_info')

    @staticmethod
    def get_brain_info_metadata_fp(stack):
        return os.path.join(DataManager.get_brain_info_root_folder(), stack + '_metadata.ini')

    @staticmethod
    def get_brain_info_progress_fp(stack):
        return os.path.join(DataManager.get_brain_info_root_folder(), stack + '_progress.ini')


    @staticmethod
    def get_brain_info_progress(stack):
        fp = DataManager.get_brain_info_progress_fp(stack)
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

    ######################################################################################################################
    #                                     ROOT FOLDERS                                                                   #
    ######################################################################################################################

    @staticmethod
    def get_images_root_folder(stack):
        #return os.path.join( os.environ['ROOT_DIR'], stack, 'preprocessing_data' )
        return os.path.join( ROOT_DIR, 'CSHL_data_processed', stack )
