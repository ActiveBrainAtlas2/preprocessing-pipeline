import os, sys
import cv2
import numpy as np
from skimage import io
from concurrent.futures.process import ProcessPoolExecutor
from abakit.lib.utilities_mask import rotate_image, pad_image, scaled, equalized
from abakit.lib.utilities_process import test_dir, SCALING_FACTOR, get_cpus
import tifffile as tiff
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from lib.pipeline_utilities import read_image,get_max_image_size
from copy import copy 
class ImageCleaner:

    def create_cleaned_images(self):
        """
        Main method that starts the cleaning/rotating process.
        :param animal:  prep_id of the animal we are working on.
        :param channel:  channel {1,2,3}
        :param flip:  flip or flop or nothing
        :param rotation: usually 1 for rotating 90 degrees
        :param full:  resolution, either full or thumbnail
        :return: nothing, writes to disk the cleaned image
        """
        if self.channel == 1:
            self.sqlController.set_task(self.animal, self.progress_lookup.CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK)
        if self.downsample:
            self.create_cleaned_images_thumbnail()
        else:
            self.create_cleaned_images_fullres()

    def create_cleaned_images_thumbnail(self):
        CLEANED = self.fileLocationManager.get_thumbnail_cleaned(self.channel)
        INPUT = self.fileLocationManager.get_thumbnail(self.channel)
        MASKS = self.fileLocationManager.thumbnail_masked
        os.makedirs(CLEANED, exist_ok=True)
        self.parallel_create_cleaned(INPUT,CLEANED,MASKS)
    
    def create_cleaned_images_fullres(self):
        CLEANED = self.fileLocationManager.get_full_cleaned(self.channel)
        os.makedirs(CLEANED, exist_ok=True)
        INPUT = self.fileLocationManager.get_full(self.channel)
        MASKS = self.fileLocationManager.full_masked
        self.parallel_create_cleaned(INPUT,CLEANED,MASKS)

    def parallel_create_cleaned(self,INPUT,CLEANED,MASKS):
        max_width,max_height = get_max_image_size(INPUT)
        rotation = self.sqlController.scan_run.rotation
        flip = self.sqlController.scan_run.flip
        test_dir(self.animal, INPUT, self.downsample, same_size=False)
        files = sorted(os.listdir(INPUT))
        progress_id = self.sqlController.get_progress_id(self.downsample, self.channel, 'CLEAN')
        self.sqlController.set_task(self.animal, progress_id)
        file_keys = []
        for file in files:
            infile = os.path.join(INPUT, file)
            outpath = os.path.join(CLEANED, file)
            if os.path.exists(outpath):
                continue
            maskfile = os.path.join(MASKS, file)
            file_keys.append([infile, outpath, maskfile, rotation, flip, max_width, max_height, self.channel])
        workers = self.get_nworkers()
        self.run_commands_in_parallel_with_executor([file_keys],workers,clean_image)


def clean_image(file_key):
    """
    This method clean all NTB images in the specified channel. For channel one it also scales
    and does an adaptive histogram equalization.
    The masks have 3 dimenions since we are using the torch process.
    The 3rd channel has what we want for the mask.
    file_keys is a tuple of the following:
        :param infile: file path of image to read
        :param outpath: file path of image to write
        :param mask: binary mask image of the image
        :param rotation: amount of rotation. 1 = rotate by 90degrees
        :param flip: either flip or flop
        :param max_width: width of image
        :param max_height: height of image
        :param scale: used in scaling. Gotten from the histogram
    :return: nothing. we write the image to disk
    """
    infile, outpath, maskfile, rotation, flip, max_width, max_height, channel = file_key
    img = read_image(infile)
    mask = read_image(maskfile)
    cleaned = apply_mask(img,mask,infile)
    if channel == 1:
        cleaned = scaled(cleaned, mask, epsilon=0.01)
        cleaned = equalized(cleaned)
    del img
    del mask
    if rotation > 0:
        cleaned = rotate_image(cleaned, infile, rotation)
    if flip == 'flip':
        cleaned = np.flip(cleaned)
    if flip == 'flop':
        cleaned = np.flip(cleaned, axis=1)
    cleaned = pad_image(cleaned, infile, max_width, max_height, 0)
    tiff.imsave(outpath, cleaned)
    del cleaned
    return

def apply_mask(img,mask,infile):
    try:
        cleaned = cv2.bitwise_and(img, img, mask=mask)
    except:
        print(f'Error in masking {infile} with mask shape {mask.shape} img shape {img.shape}')
        print('Are the shapes exactly the same?')
        print("Unexpected error:", sys.exc_info()[0])
        raise
    return cleaned