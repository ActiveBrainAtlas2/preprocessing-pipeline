from Litao.post_czi_processor import PostCZIProcessor
from Litao.post_tif_processor import PostTIFProcessor

post_czi_processor = PostCZIProcessor('DK52')
#post_czi_processor.make_tif_datajoint()
#post_czi_processor.make_histogram_datajoint()
#post_czi_processor.make_thumbnail_datajoint()
#post_czi_processor.make_thumbnail_web_datajoint()

post_tif_processor = PostTIFProcessor('DK52', False)
#post_tif_processor.preprocess_prep_dir()
#post_tif_processor.make_mask_datajoint()
#post_tif_processor.apply_mask_datajoint('NTB', 0, 'flip')