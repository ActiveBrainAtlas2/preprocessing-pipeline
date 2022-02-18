import os
import cv2
import numpy as np
from skimage import io
from lib.utilities_mask import equalized

class Normalizer:
    def create_normalization(self):
        INPUT = self.fileLocationManager.thumbnail
        OUTPUT = self.fileLocationManager.get_normalized(self.channel)
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

