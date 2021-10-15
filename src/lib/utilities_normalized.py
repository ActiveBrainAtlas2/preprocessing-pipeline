import os

import cv2
import numpy as np
from skimage import io
from lib.file_location import FileLocationManager
from lib.utilities_mask import equalized


def create_normalization(animal, channel):
    fileLocationManager = FileLocationManager(animal)
    INPUT = fileLocationManager.thumbnail
    OUTPUT = os.path.join(fileLocationManager.prep, f'CH{channel}', 'normalized')
    os.makedirs(OUTPUT, exist_ok=True)
    files = sorted(os.listdir(INPUT))
    for file in files:
        infile = os.path.join(INPUT, file)
        outpath = os.path.join(OUTPUT, file)
        if os.path.exists(outpath):
            continue

        img = io.imread(infile)

        if img.dtype == np.uint16:
            img = (img/256).astype(np.uint8)

        fixed = equalized(img)
        cv2.imwrite(outpath, fixed.astype(np.uint8))

