from pathlib import Path

def get_data_save_folder():
    return '~/data/'

def get_plot_save_path_root():
    return '~/plots/'

def get_path_to_prep_images():
    return Path('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data')

def get_path_to_affine_transformed_images():
    return Path('~/data/Affine_transformed_thumbnails/')

def get_subpath_to_tif_files(brain_id):
    data_dir = get_path_to_prep_images()
    return data_dir / brain_id / 'preps/CH1/thumbnail_aligned'

def get_subpath_to_thumb_nails(brain_id):
    data_dir = get_path_to_prep_images()
    return data_dir / brain_id / 'preps/CH1/thumbnail_aligned'

def get_subpath_to_affine_transformed_thumbnails(brain_id):
    data_dir = get_path_to_affine_transformed_images()
    return data_dir / brain_id 