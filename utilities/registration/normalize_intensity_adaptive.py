import argparse
import sys
import os
from skimage import io, img_as_ubyte
import numpy as np
import cv2
from tqdm import tqdm
from skimage.exposure import rescale_intensity, adjust_gamma

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager
from utilities.utilities_mask import resample_scoremap, rescale_by_resampling

gamma_map = img_as_ubyte(adjust_gamma(np.arange(0, 256, 1) / 256., 8.))
low = -2.
high = 50.


def run_normalize(animal, channel):

    fileLocationManager = FileLocationManager(animal)
    channel_dir = f'CH{channel}'
    INPUT = os.path.join(fileLocationManager.prep, channel_dir, 'thumbnail')
    OUTPUT = os.path.join(fileLocationManager.prep, channel_dir, 'normalized')
    MASKS = os.path.join(fileLocationManager.prep, 'thumbnail_masked')
    files = sorted(os.listdir(INPUT))
    for file in tqdm(files):

        img = io.imread(os.path.join(INPUT, file))
        img = (img/256).astype(np.uint8)
        raw_mask = io.imread(os.path.join(MASKS, file))
        mean_std_all_regions = []
        cx_cy_all_regions = []
        region_size = 600
        region_spacing = 300
        for cx in range(0, img.shape[1], region_spacing):
            for cy in range(0, img.shape[0], region_spacing):
                region = img[max(cy-region_size//2, 0):min(cy+region_size//2+1, img.shape[0]-1),
                             max(cx-region_size//2, 0):min(cx+region_size//2+1, img.shape[1]-1)]
                region_mask = raw_mask[max(cy-region_size//2, 0):min(cy+region_size//2+1, img.shape[0]-1),
                                       max(cx-region_size//2, 0):min(cx+region_size//2+1, img.shape[1]-1)]
                if np.count_nonzero(region_mask) == 0:
                    continue
                mean_std_all_regions.append((region[region_mask].mean(), region[region_mask].std()))
                cx_cy_all_regions.append((cx, cy))

        mean_map = resample_scoremap(sparse_scores=np.array(mean_std_all_regions)[:,0],
                                 sample_locations=cx_cy_all_regions,
                                 gridspec=(region_size, region_spacing, img.shape[1], img.shape[0], (0,0)),
                                 downscale=4,
                                 interpolation_order=2)


        mean_map = rescale_by_resampling(mean_map, new_shape=(img.shape[1], img.shape[0]))

        std_map = resample_scoremap(sparse_scores=np.array(mean_std_all_regions)[:,1],
                                 sample_locations=cx_cy_all_regions,
                                 gridspec=(region_size, region_spacing, img.shape[1], img.shape[0], (0,0)),
                                 downscale=4,
                                 interpolation_order=2)

        std_map = rescale_by_resampling(std_map, new_shape=(img.shape[1], img.shape[0]))
        # Save mean/std results.
        #np.savetxt(fp, cx_cy_all_regions)
        #np.savetxt(fp, mean_std_all_regions)
        #np.save( fp, mean_map.astype(np.float16))
        #np.save( fp, std_map.astype(np.float16))
        raw_mask = raw_mask & (std_map > 0)
        img_normalized = np.zeros(img.shape, np.float32)
        #print(mean_map[raw_mask], std_map[raw_mask])
        img_normalized[raw_mask] = (img[raw_mask] - mean_map[raw_mask]) / std_map[raw_mask]
        # save img_normalized
        img_normalized_uint8 = rescale_intensity(img_normalized.astype(np.float), (low, high), (0, 2**8-1)).astype(np.uint8)

        #img_normalized_uint8 = rescale_intensity_v2(img_normalized, low, high)
        #img_normalized_uint8[~raw_mask] = 0

        img = 255 - img_normalized_uint8



        #####fixed = gamma_map[img]
        fixed = img.copy()
        outpath = os.path.join(OUTPUT, file)
        cv2.imwrite(outpath, fixed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal animal', required=True)
    parser.add_argument('--channel', help='Enter channel', required=True)

    args = parser.parse_args()
    animal = args.animal
    channel = args.channel
    run_normalize(animal, channel)
