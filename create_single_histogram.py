import argparse
import os, sys
from collections import Counter
from matplotlib import pyplot as plt
from skimage import io
import cv2

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)

# no preprocessing on channels 2 and 3
# above 2000 are the high colored cells
#1300 - 4200 is the important stuff
# add a histogram below the normalization slider
# for the individual section
input_path = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK55/preps/CH3/thumbnail/175.tif'
mask_path = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK55/preps/thumbnail_masked/175.tif'
output_path = os.path.join(HOME, '175.green.tif')

img = io.imread(input_path)
mask = io.imread(mask_path)

img = cv2.bitwise_and(img, img, mask=mask)


flat = img.flatten()

fig = plt.figure()
plt.rcParams['figure.figsize'] = [10, 6]
plt.hist(flat, flat.max(), [0, 10000], color='r')
plt.style.use('ggplot')
plt.yscale('log')
plt.grid(axis='y', alpha=0.75)
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title(f'175 @16bit')
plt.close()
fig.savefig(output_path, bbox_inches='tight')
