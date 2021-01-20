
import os, sys
import shutil
from tqdm import tqdm
import imagesize
import numpy as np
from PIL import Image

from cloudvolume import CloudVolume

from taskqueue import LocalTaskQueue
import igneous.task_creation as tc

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager


def make_info_file(volume_size,resolution,layer_dir,commit=True):
    """
    ---PURPOSE---
    Make the cloudvolume info file.
    ---INPUT---
    volume_size     [Nx,Ny,Nz] in voxels, e.g. [2160,2560,1271]
    resolution      [nm/pix in x,nm/pix in y,nm/pix in z]
    pix_scale_nm    [size of x pix in nm,size of y pix in nm,size of z pix in nm], e.g. [5000,5000,10000]
    commit          if True, will write the info/provenance file to disk.
                    if False, just creates it in memory
    """
    info = CloudVolume.create_new_info(
        num_channels = 1,
        layer_type = 'segmentation', # 'image' or 'segmentation'
        data_type = 'uint16', #
        encoding = 'raw', # other options: 'jpeg', 'compressed_segmentation' (req. uint32 or uint64)
        resolution = resolution, # Size of X,Y,Z pixels in nanometers,
        voxel_offset = [ 0, 0, 0 ], # values X,Y,Z values in voxels
        chunk_size = [ 1024,1024,1 ], # rechunk of image X,Y,Z in voxels -- only used for downsampling task I think
        volume_size = volume_size, # X,Y,Z size in voxels
        )

    vol = CloudVolume(f'file://{layer_dir}', info=info, compress=False)
    vol.provenance.description = "Test on spock for profiling precomputed creation"
    vol.provenance.owners = ['eodonnell'] # list of contact email addresses
    if commit:
        vol.commit_info() # generates info json file
        vol.commit_provenance() # generates provenance json file
        print("Created CloudVolume info file: ",vol.info_cloudpath)
    return vol

def process_slice(i, z):
    """
    ---PURPOSE---
    Upload a tif slice image to cloudvolume
    ---INPUT---
    z          The 0-indexed integer representing the slice number
    """
    fileLocationManager = FileLocationManager('X')
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/downsampled_cropped')
    OUTPUT_DIR = os.path.join(fileLocationManager.prep, 'CH1/processed')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.path.exists(os.path.join(OUTPUT_DIR, z)):
        print(f"Slice {z} already processed, skipping ")
        return
    img_name = os.path.join(INPUT, z)
    image = Image.open(img_name)
    width, height = image.size
    array = np.array(image, dtype=np.uint16, order='F')
    array = array.reshape((1, height, width)).T
    vol[:,:, i] = array
    image.close()
    return

if __name__ == "__main__":
    # make a list of your slices
    fileLocationManager = FileLocationManager('X')
    INPUT = os.path.join(fileLocationManager.prep, 'CH1/downsampled_cropped')
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))
    #files = files[1000:1200]

    midpoint = len(files) // 2
    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)
    x_dim = width
    y_dim = height
    z_dim = len(files)

    # Make the info file
    x_scale_nm, y_scale_nm,z_scale_nm = 2000,2000,1000

    """ Handle the different steps """
    volume_size = (x_dim,y_dim,z_dim)
    resolution = (x_scale_nm,y_scale_nm,z_scale_nm)

    vol = make_info_file(volume_size=volume_size,layer_dir=OUTPUT_DIR,resolution=resolution)
    print(f"Have {len(files)} planes to upload")
    # Upload slices in parallel to cloudvolume
    #with ProcessPoolExecutor(max_workers=2) as executor:
    #    executor.map(process_slice, to_upload)
    #    vol.cache.flush()
    for i, z in enumerate(tqdm(files)):
        process_slice(i, z)



