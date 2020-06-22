"""
This file will create masks from channel 1 of the thumbnails.
"""
import os
import argparse
import cv2
import numpy as np
from skimage import io
from tqdm import tqdm

from utilities.file_location import FileLocationManager
from Litao.utilities_mask import get_last_2d, remove_strip, find_threshold, find_main_blob, scale_and_mask


def make_mask(img):
    img = get_last_2d(img)
    no_strip, fe = remove_strip(img)

    # Threshold it so it becomes binary
    min_value, threshold = find_threshold(img)
    # threshold = 272
    ret, threshed = cv2.threshold(no_strip, threshold, 255, cv2.THRESH_BINARY)
    threshed = np.uint8(threshed)

    # Find connected elements
    # You need to choose 4 or 8 for connectivity type
    connectivity = 4
    output = cv2.connectedComponentsWithStats(threshed, connectivity, cv2.CV_32S)
    # Get the results
    # The first cell is the number of labels
    num_labels = output[0]
    # The second cell is the label matrix
    labels = output[1]
    # The third cell is the stat matrix
    stats = output[2]
    # The fourth cell is the centroid matrix
    centroids = output[3]
    # Find the blob that corresponds to the section.
    row = find_main_blob(stats, img)
    blob_label = row[1]['blob_label']
    # extract the blob
    blob = np.uint8(labels == blob_label) * 255
    # Perform morphological closing
    kernel10 = np.ones((10, 10), np.uint8)
    closing = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel10, iterations=5)
    del blob
    if fe != 0:
        img[:, fe:] = 0  # mask the strip
    # scale and mask
    scaled, _max = scale_and_mask(img, closing)

    return closing, scaled


def make_mask_file(input_path, masked_path, cleaned_path):
    try:
        img = io.imread(input_path)
    except:
        print('Could not open', input_path)
        return False

    closing, scaled = make_mask(img)

    try:
        os.makedirs(os.path.dirname(masked_path), exist_ok=True)
        cv2.imwrite(masked_path, closing.astype('uint8'))
    except:
        print('Could not write', masked_path)
        return False

    try:
        os.makedirs(os.path.dirname(cleaned_path), exist_ok=True)
        cv2.imwrite(cleaned_path, scaled.astype('uint16'))
    except:
        print('Could not write', cleaned_path)
        return False

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)

    args = parser.parse_args()
    animal = args.animal

    file_location_manager = FileLocationManager(animal)
    input_dir = os.path.join(file_location_manager.prep, 'CH1', 'thumbnail')
    masked_dir = os.path.join(file_location_manager.prep, 'masked')
    cleaned_dir = os.path.join(file_location_manager.prep, 'CH1', 'cleaned')

    for file_name in tqdm(sorted(os.listdir(input_dir))):
        input_path = os.path.join(input_dir, file_name)
        masked_path = os.path.join(masked_dir, file_name)
        cleaned_path = os.path.join(cleaned_dir, file_name)

        make_mask_file(input_path, masked_path, cleaned_path)
