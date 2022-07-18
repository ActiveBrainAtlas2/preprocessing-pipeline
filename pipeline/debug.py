import os, sys, psutil
from debugpy import breakpoint
import cv2
import numpy as np
from skimage import io
from concurrent.futures.process import ProcessPoolExecutor
from utilities.utilities_mask import rotate_image, pad_image, scaled, equalized
from utilities.utilities_process import test_dir, SCALING_FACTOR, get_cpus
import tifffile as tiff
from PIL import Image
from time import time
import os, psutil
process = psutil.Process(os.getpid())
print(process.memory_info().rss*10e-10) 

Image.MAX_IMAGE_PIXELS = None
from lib.pipeline_utilities import read_image, get_max_image_size, convert_size
from model.slide import SlideCziTif
from model.slide import Slide
from model.slide import Section
from copy import copy
from pathlib import Path
import operator
import gc
from timeit import default_timer as timer
def apply_mask(img, mask, infile):
    try:
        cleaned = cv2.bitwise_and(img, img, mask=mask)
    except:
        print(
            f"Error in masking {infile} with mask shape {mask.shape} img shape {img.shape}"
        )
        print("Are the shapes exactly the same?")
        print("Unexpected error:", sys.exc_info()[0])
        raise
    return cleaned

def process_image(n, queue, uuid):
    my_pid = os.getpid()
    queue.put((uuid, my_pid))
    file_key = ['/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK78/preps/CH1/full/194.tif', '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK78/preps/CH1/full_cleaned/194.tif', '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK78/preps/full_masked/194.tif', 3, 'none', 30000, 60000, 1]
    infile, outpath, maskfile, rotation, flip, max_width, max_height, channel = file_key
    print("load image")
    img = read_image(infile)
    print("load mask")
    mask = read_image(maskfile)
    print("apply mask")
    cleaned = apply_mask(img, mask, infile)
    print("scale")
    cleaned = scaled(cleaned, mask, epsilon=0.01)
    print("equalize")
    cleaned = equalized(cleaned)
    del img
    del mask
    print("image and masks deleted")
    print("rotate")
    cleaned = rotate_image(cleaned, infile, rotation)
    print("flip")
    cleaned = np.flip(cleaned)
    print("pad")
    cropped = pad_image(cleaned, infile, max_width, max_height, 0)
    del cropped
    print("cropped deleted")

from concurrent.futures import ProcessPoolExecutor
import os
import time 
import uuid
#from multiprocessing import Process, Queue
import multiprocessing
import queue
#The Empty exception in in Queue, multiprocessing borrows 
#it from there

# https://stackoverflow.com/questions/9908781/sharing-a-result-queue-among-several-processes     
m = multiprocessing.Manager()
q = m.Queue()

def task(n, queue, uuid):
    my_pid = os.getpid()
    print("Executing our Task on Process {}".format(my_pid))
    queue.put((uuid, my_pid))
    time.sleep(n)
    return n * n

def main():

    with ProcessPoolExecutor(max_workers = 3) as executor:

        some_dict = {}
        for i in range(1):
            print(i)

            u = uuid.uuid4()
            f = executor.submit(process_image, i, q, u)
            some_dict[u] = [f, None] # PID not known here

            try:
                rcv_uuid, rcv_pid = q.get(block=True, timeout=1)
                some_dict[rcv_uuid][1] = rcv_pid # store PID
            except queue.Empty as e:
                print('handle me', e)
            print('I am', rcv_uuid, 'and my PID is', rcv_pid)
        process = psutil.Process(rcv_pid)
        while not f.done() :
            print(process.memory_info().rss*10e-10) 
            time.sleep(1)



if __name__ == '__main__':
    main()