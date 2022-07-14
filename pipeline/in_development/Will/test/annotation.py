from PIL import Image
Image.MAX_IMAGE_PIXELS = 3000000000
im = Image.open('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK55/preps/CH3/full_aligned/180.tif')
im.size