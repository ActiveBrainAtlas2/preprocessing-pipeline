import numpy as np
from matplotlib import pyplot as plt
from skimage import io
from os.path import expanduser
HOME = expanduser("~")
import os

from tqdm import tqdm
from collections import Counter
stack = 'DK39'
channel = 1
DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/{}'.format(stack)
#DIR = '/data2/edward/{}'.format(stack)
INPUT = os.path.join(DIR, 'preps', 'aligned')
files = os.listdir(INPUT)
lfiles = len(files)
print(lfiles)




hist_dict = Counter({})
for file in tqdm(files):
    filepath = os.path.join(INPUT,file)
    try:
        img = io.imread(filepath)
    except:
        print('cannot read file',file)
        lfiles -= 1
        break
    try:
        flat = img.flatten()
        #flat = np.random.choice(flat, 1000)
        del img
    except:
        print('cannot flatten file',file)
        lfiles -= 1
        break
    try:
        #hist,bins = np.histogram(flat, bins=nbins)
        img_counts = np.bincount(flat)
    except:
        print('could not create counts',file)
        lfiles -= 1
        break
    try:
        img_dict = Counter(dict(zip(np.unique(flat), img_counts[img_counts.nonzero()])))
    except:
        print('could not create counter',file)
        lfiles -= 1
        break
    try:
        hist_dict = hist_dict + img_dict
    except:
        print('could not add files',file)
        lfiles -= 1
        break


hist_dict = dict(hist_dict)
hist_values = [i/lfiles for i in hist_dict.values()]

colors = {1:'b', 2:'r', 3:'g'}
fig = plt.figure()
plt.rcParams['figure.figsize'] = [10, 6]
plt.bar(list(hist_dict.keys()), hist_values, color = colors[channel])
plt.yscale('log')
plt.grid(axis='y', alpha=0.75)
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title('{} channel {} @16bit with {} tif files'.format(stack, channel, lfiles))
outfile = '{}_C{}.histogram.png'.format(stack, channel)
fig.savefig(outfile, bbox_inches='tight')


