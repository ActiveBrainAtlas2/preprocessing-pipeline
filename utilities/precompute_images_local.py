import os
import sys
import json
from PIL import Image, ImageOps
import math
import numpy as np
from skimage import io

from skimage import io
from neuroglancer_scripts.scripts import (generate_scales_info,
                                          slices_to_precomputed,
                                          compute_scales)

from os.path import expanduser
HOME = expanduser("~")

DIR = os.path.join(HOME, 'programming', 'dk39', 'preps')
#DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39/preps'
NEUROGLANCER = os.path.join(DIR, 'neuroglancer')
RESIZED = os.path.join(DIR, 'resized')
PADDED = os.path.join(DIR, 'padded')
INPUT = os.path.join(DIR, 'oriented')

def unlink_file(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))



def resize_canvas(old_image_path, new_image_path,
                  canvas_width=500, canvas_height=500):
    """
    Resize the canvas of old_image_path.
    Store the new image in new_image_path. Center the image on the new canvas.
    Parameters
    ----------
    old_image_path : str
    new_image_path : str
    canvas_width : int
    canvas_height : int
    """
    im = Image.open(old_image_path)

    #im = ImageOps.equalize(imag)


    old_width, old_height = im.size
    # Center the image
    x1 = int(math.floor((canvas_width - old_width) / 2))
    y1 = int(math.floor((canvas_height - old_height) / 2))

    mode = im.mode
    if len(mode) == 1:  # L, 1
        new_background = (255)
    if len(mode) == 3:  # RGB
        new_background = (255, 255, 255)
    if len(mode) == 4:  # RGBA, CMYK
        new_background = (255, 255, 255, 255)
    #newImage = Image.new(mode, (canvas_width, canvas_height), new_background)
    newImage = Image.new(mode, (canvas_width, canvas_height))
    newImage.paste(im, (x1, y1, x1 + old_width, y1 + old_height))
    newImage.save(new_image_path)

    #im = Image.open(infile)
    #im.thumbnail(size)
    #im.save(file + ".thumbnail", "JPEG")

def get_max_size(INPUT):
    widths = []
    heights = []
    files = os.listdir(INPUT)
    for file in files:
        img = io.imread(os.path.join(INPUT, file))
        heights.append(img.shape[0])
        widths.append(img.shape[1])
        img = None

    max_width = max(widths)
    max_height = max(heights)

    return max_width, max_height

def convert_to_precomputed(folder_to_convert_from, folder_to_convert_to):

    # ---------------- Conversion to precomputed format ----------------
    voxel_resolution=[460, 460, 20000]
    voxel_offset=[0, 0, 0]

    info_fullres_template = {
        "type": "image",
        "num_channels": None,
        "scales": [{
            "chunk_sizes": [],
            "encoding": "raw",
            "key": "full",
            "resolution": [None, None, None],
            "size": [None, None, None],
            "voxel_offset": voxel_offset}],
        "data_type": None}

    # make a folder under the "precomputed" dir and execute conversion routine
    if not os.path.isdir(folder_to_convert_from):
        raise NotADirectoryError
    # make a corresponding folder in the "precomputed_dir"
    if not os.path.exists(folder_to_convert_to):
        os.makedirs(folder_to_convert_to)
    # read 1 image to get the shape
    imgs = os.listdir(folder_to_convert_from)
    img = io.imread(os.path.join(folder_to_convert_from, imgs[0]))
    # write info_fullres.json
    info_fullres = info_fullres_template.copy()
    info_fullres['scales'][0]['size'] = [img.shape[1], img.shape[0], len(imgs)]
    info_fullres['scales'][0]['resolution'] = voxel_resolution
    info_fullres['num_channels'] = img.shape[2] if len(img.shape) > 2 else 1
    info_fullres['data_type'] = str(img.dtype)
    with open(os.path.join(folder_to_convert_to, 'info_fullres.json'), 'w') as outfile:
        json.dump(info_fullres, outfile)

    # --- neuroglancer-scripts routine ---
    #  generate_scales_info - make info.json
    generate_scales_info.main(['', os.path.join(folder_to_convert_to, 'info_fullres.json'),
                               folder_to_convert_to])
    # slices_to_precomputed - build the precomputed for the fullress
    slices_to_precomputed.main(
        ['', folder_to_convert_from, folder_to_convert_to, '--flat', '--no-gzip'])
    # compute_scales - build the precomputed for other scales
    compute_scales.main(['', folder_to_convert_to, '--flat', '--no-gzip'])



def main(argv=sys.argv):
    Image.MAX_IMAGE_PIXELS = None
    #convert_to_precomputed()

    #canvas_width = 51932
    #canvas_height = 24275
    """
    canvas_width, canvas_height = get_avg_size()
    print('w and h:', canvas_width, canvas_height)
    for img in os.listdir(ALIGNED):
        original_image = os.path.join(ALIGNED, img)
        new_file = os.path.join(RESIZED, img)
        resize_canvas(original_image, new_file, canvas_width, canvas_height)
    """
    convert_to_precomputed(RESIZED, NEUROGLANCER)

if __name__ == "__main__":
    sys.exit(main())
