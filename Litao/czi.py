import argparse

from utilities.post_czi_processor import PostCZIProcessor
from utilities.post_tif_processor import PostTIFProcessor




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal ID', required=True)
    args = parser.parse_args()
    animal = args.animal
    post_czi_processor = PostCZIProcessor(animal)
    # post_czi_processor.make_tif_datajoint()
    # post_czi_processor.make_histogram_datajoint()
    # post_czi_processor.make_thumbnail_datajoint()
    # post_czi_processor.make_thumbnail_web_datajoint()

    #post_tif_processor = PostTIFProcessor('DK52', False)
    # post_tif_processor.preprocess_prep_dir()
    # post_tif_processor.make_mask_datajoint()
    # post_tif_processor.apply_mask_datajoint('NTB', 0, 'flip')
