import json
import os, sys
import shutil
from concurrent.futures import ProcessPoolExecutor
from skimage import io

from tqdm import tqdm
import imagesize
import numpy as np
from PIL import Image

from cloudvolume import CloudVolume

from taskqueue import LocalTaskQueue
import igneous.task_creation as tc

from utilities.utilities_cvat_neuroglancer import get_cpus

HOME = os.path.expanduser("~")
PATH = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(PATH)
from utilities.file_location import FileLocationManager

DIR = 'CH1/thumbnail_aligned'


def add_segment_properties(precomputed_vol, segment_properties):
    precomputed_vol.info['segment_properties'] = 'names'
    precomputed_vol.commit_info()

    segment_properties_path = os.path.join(precomputed_vol.layer_cloudpath.replace('file://', ''), 'names')
    os.makedirs(segment_properties_path, exist_ok=True)

    info = {
        "@type": "neuroglancer_segment_properties",
        "inline": {
            "ids": [str(number) for number, label in segment_properties],
            "properties": [{
                "id": "label",
                "type": "label",
                "values": [str(label) for number, label in segment_properties]
            }]
        }
    }
    with open(os.path.join(segment_properties_path, 'info'), 'w') as file:
        json.dump(info, file, indent=2)


def add_downsampled_volumes(precomputed_vol):
    cpus = get_cpus()
    tq = LocalTaskQueue(parallel=cpus)
    tasks = tc.create_downsampling_tasks(precomputed_vol.layer_cloudpath, compress=False)
    tq.insert(tasks)
    tq.execute()


def add_segmentation_mesh(precomputed_vol):
    cpus = get_cpus()
    tq = LocalTaskQueue(parallel=cpus)
    tasks = tc.create_meshing_tasks(precomputed_vol.layer_cloudpath, mip=0,
                                    compress=False)  # The first phase of creating mesh
    tq.insert(tasks)
    tq.execute()

    # It should be able to incoporated to above tasks, but it will give a weird bug. Don't know the reason
    tasks = tc.create_mesh_manifest_tasks(precomputed_vol.layer_cloudpath)  # The second phase of creating mesh
    tq.insert(tasks)
    tq.execute()


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
        data_type = 'uint8', #
        encoding = 'raw', # other options: 'jpeg', 'compressed_segmentation' (req. uint32 or uint64)
        resolution = resolution, # Size of X,Y,Z pixels in nanometers,
        voxel_offset = [ 0, 0, 0 ], # values X,Y,Z values in voxels
        chunk_size = [1024, 1024, 1 ], # rechunk of image X,Y,Z in voxels -- only used for downsampling task I think
        volume_size = volume_size, # X,Y,Z size in voxels
        )

    volume = CloudVolume(f'file://{layer_dir}',mip=0, info=info, compress=False, progress=False)
    volume.provenance.description = "Creating a mesh"
    volume.provenance.owners = ['eodonnell'] # list of contact email addresses
    if commit:
        volume.commit_info() # generates info json file
        volume.commit_provenance() # generates provenance json file
        print("Created CloudVolume info file: ",volume.info_cloudpath)
    return volume

def process_slice(file_key):
    """
    ---PURPOSE---
    Upload a tif slice image to cloudvolume
    ---INPUT---
    z          The 0-indexed integer representing the slice number
    """
    index, filename = file_key
    fileLocationManager = FileLocationManager('X')
    INPUT = os.path.join(fileLocationManager.prep, DIR)

    #img_name = os.path.join(INPUT, filename)
    #image = Image.open(img_name)
    #width, height = image.size
    #array = np.array(image, dtype=np.uint8, order='F')
    #array = array.reshape((1, height, width)).T
    #print('PIL',filename, array.shape)
    ##volume[:,:, index] = array
    #image.close()

    infile = os.path.join(INPUT, filename)
    tif = io.imread(infile)
    tif = tif.reshape(tif.shape[1], tif.shape[0], 1)
    #print('IO ',filename, tif.shape)
    volume[:,:,index] = tif

    return

if __name__ == "__main__":
    # make a list of your slices
    fileLocationManager = FileLocationManager('X')
    INPUT = os.path.join(fileLocationManager.prep, DIR)
    OUTPUT_DIR = os.path.join(fileLocationManager.neuroglancer_data, 'mesh')
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(INPUT))
    #files = files[0:1000]

    midpoint = len(files) // 2

    midfilepath = os.path.join(INPUT, files[midpoint])
    width, height = imagesize.get(midfilepath)
    x_dim = width
    y_dim = height

    #files = files[midpoint-300:midpoint+300]

    z_dim = len(files)
    volume_size = (x_dim,y_dim,z_dim)
    resolution = (10000, 10000, 1000) # in nm

    volume = make_info_file(volume_size=volume_size,layer_dir=OUTPUT_DIR,resolution=resolution)
    print(f"Have {len(files)} planes to upload")
    file_keys = []
    for i, f in enumerate(tqdm(files)):
        file_keys.append([i,f])

    workers = get_cpus()
    with ProcessPoolExecutor(max_workers=workers) as executor:
        executor.map(process_slice, file_keys)
        volume.cache.flush()

    add_downsampled_volumes(volume)
    add_segmentation_mesh(volume)





