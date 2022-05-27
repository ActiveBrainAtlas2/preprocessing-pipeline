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
        This method applies the image masks that has been edited by the user to extract the tissue image from the surrounding
        debre
        """
        if self.channel == 1:
            self.sqlController.set_task(self.animal, self.progress_lookup.CLEAN_CHANNEL_1_THUMBNAIL_WITH_MASK)
        if self.downsample:
            self.create_cleaned_images_thumbnail()
        else:
            self.create_cleaned_images_full_resolution()

    def create_cleaned_images_thumbnail(self):
        """Clean the image using the masks for the downsampled version"""
        CLEANED = self.fileLocationManager.get_thumbnail_cleaned(self.channel)
        INPUT = self.fileLocationManager.get_thumbnail(self.channel)
        MASKS = self.fileLocationManager.thumbnail_masked
        os.makedirs(CLEANED, exist_ok=True)
        self.parallel_create_cleaned(INPUT,CLEANED,MASKS)
    
    def create_cleaned_images_full_resolution(self):
        """Clean the image using the masks for the full resolution image"""
        CLEANED = self.fileLocationManager.get_full_cleaned(self.channel)
        os.makedirs(CLEANED, exist_ok=True)
        INPUT = self.fileLocationManager.get_full(self.channel)
        MASKS = self.fileLocationManager.full_masked
        self.parallel_create_cleaned(INPUT,CLEANED,MASKS)

    def parallel_create_cleaned(self,INPUT,CLEANED,MASKS):
        """Clean the images (downsampled or full size) in parallel"""
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
        self.run_commands_in_parallel_with_executor([file_keys],workers,clean_and_rotate_image)


def clean_and_rotate_image(file_key):
    """    The main function that uses the User edited mask to crop out the tissue from surrounding debre. and rotates the image to
           a usual orientation (where the olfactory bulb is facing left and the cerebellum is facing right.  
           The hippocampus is facing up and the brainstem is facing down)
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

    Args:
        file_key (list): List of arguments parsed to the cropping algorithm.  includes:
        1. str: path to the tiff file being cropped
        2. str: path to store the cropped tiff image
        3. str: path to the mask file used to crop the image
        4. int: Number of rotations to be applied .  The rotation is user defined and was used to make sure the brain is
                in a usual orientation that makes sense. each rotation is 90 degree
                eg: a rotation of 3 is a 270 degree rotation
        5. int: 
    """    
    infile, outpath, maskfile, rotation, flip, max_width, max_height, channel = file_key
    img = read_image(infile)
    mask = read_image(maskfile)
    cleaned = apply_mask(img,mask,infile)
    if channel == 1:
        cropped = scaled(cropped, mask, epsilon=0.01)
        cropped = equalized(cropped)
    cropped = crop_image(cleaned,mask)
    del img
    del mask
    if rotation > 0:
        cropped = rotate_image(cropped, infile, rotation)
    if flip == 'flip':
        cropped = np.flip(cropped)
    if flip == 'flop':
        cropped = np.flip(cropped, axis=1)
    cropped = pad_image(cropped, infile, max_width, max_height, 0)
    tiff.imsave(outpath, cropped)
    del cropped
    return

def crop_image(img, mask):
    BUFFER = 2
    mask = np.array(mask)
    mask[mask > 0] = 255
    ret, thresh = cv2.threshold(mask, 200, 255, 0)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        if area > 100:
            xmin = int(round(x))
            ymin = int(round(y))
            xmax = int(round(x+w))
            ymax = int(round(y+h))
            boxes.append([xmin, ymin, xmax, ymax])
    x1 = min(x[0] for x in boxes) - BUFFER
    y1 = min(x[1] for x in boxes) - BUFFER
    x2 = max(x[2] for x in boxes) + BUFFER
    y2 = max(x[3] for x in boxes) + BUFFER
    img = np.ascontiguousarray(img, dtype=np.uint16)
    cropped = img[y1:y2, x1:x2] 
    return cropped

def apply_mask(img,mask,infile):
    try:
        cleaned = cv2.bitwise_and(img, img, mask=mask)
    except:
        print(f'Error in masking {infile} with mask shape {mask.shape} img shape {img.shape}')
        print('Are the shapes exactly the same?')
        print("Unexpected error:", sys.exc_info()[0])
        raise
    return cleaned