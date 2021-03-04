import os
import sys
from skimage import measure
from skimage import io
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import cv2
import json
import socket
import numpy as np
import neuroglancer
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
from cloudvolume.lib import touch
from pathlib import Path
from matplotlib import colors
from pylab import cm
from collections import defaultdict

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())
from utilities.sqlcontroller import SqlController

def get_cpus():
    usecpus = (4,4)
    cpus = {}
    cpus['muralis'] = (16,40)
    cpus['basalis'] = (12,12)
    cpus['ratto'] = (10,10)
    hostname = socket.gethostname()
    hostname = hostname.split(".")[0]
    if hostname in cpus.keys():
        usecpus = cpus[hostname]
    return usecpus

def calculate_chunks(downsample, mip):
    """
    Chunks default to 64,64,64 so we want different chunks at 
    different resolutions
    """
    d = defaultdict(dict)
    result = [64,64,64]
    d['full'][0] = [1024,1024,1]
    d['full'][1] = [256,256,8]
    d['full'][2] = [128,128,8]
    d['full'][3] = [128,128,16]
    d['full'][4] = [128,128,32]
    d['full'][5] = [64,64,64]
    d['full'][6] = [64,64,64]
    d['full'][7] = [64,64,64]
    d['full'][8] = [64,64,64]
    d['full'][9] = [64,64,64]

    d['thumbnail'][0] = [256,256,1]
    d['thumbnail'][1] = [128,128,64]
    d['thumbnail'][2] = [64,64,64]
    d['thumbnail'][3] = [64,64,64]
    try:
        result = d[downsample][mip]
    except:
        result = [64,64,64]
    return result

def calculate_factors(downsample, mip):
    """
    Scales get calculated by default by 2x2x1 downsampling
    """
    d = defaultdict(dict)
    result = [2,2,1]
    d['full'][0] = result
    d['full'][1] = result
    d['full'][2] = result
    d['full'][3] = result
    d['full'][4] = result
    d['full'][5] = result
    d['full'][6] = result
    d['full'][7] = [2,2,2]
    d['full'][8] = [2,2,2]
    d['full'][9] = [2,2,2]

    d['thumbnail'][0] = [2,2,1]
    d['thumbnail'][1] = [2,2,1]
    d['thumbnail'][2] = [2,2,1]
    d['thumbnail'][3] = [2,2,1]
    try:
        result = d[downsample][mip]
    except:
        result = [2,2,1]
    return result






def get_db_structure_infos():
    sqlController = SqlController('MD589')
    db_structures = sqlController.get_structures_dict()
    structures = {}
    for structure, v in db_structures.items():
        if '_' in structure:
            structure = structure[0:-2]
        structures[structure] = v
    return structures

def get_known_foundation_structure_names():
    known_foundation_structures = ['MVePC', 'DTgP', 'VTA', 'Li', 'Op', 'Sp5C', 'RPC', 'MVeMC', 'APT', 'IPR',
                                   'Cb', 'pc', 'Amb', 'SolIM', 'Pr5VL', 'IPC', '8n', 'MPB', 'Pr5', 'SNR',
                                   'DRD', 'PBG', '10N', 'VTg', 'R', 'IF', 'RR', 'LDTg', '5TT', 'Bar',
                                   'Tz', 'IO', 'Cu', 'SuVe', '12N', '6N', 'PTg', 'Sp5I', 'SNC', 'MnR',
                                   'RtTg', 'Gr', 'ECu', 'DTgC', '4N', 'IPA', '3N', '7N', 'LC', '7n',
                                   'SC', 'LPB', 'EW', 'Pr5DM', 'VCA', '5N', 'Dk', 'DTg', 'LVe', 'SpVe',
                                   'MVe', 'LSO', 'InC', 'IC', 'Sp5O', 'DC', 'Pn', 'LRt', 'RMC', 'PF',
                                   'VCP', 'CnF', 'Sol', 'IPL', 'X', 'AP', 'MiTg', 'DRI', 'RPF', 'VLL']
    return known_foundation_structures

def get_structure_number(structure):
    db_structure_infos = get_db_structure_infos()
    known_foundation_structure_names = get_known_foundation_structure_names()
    non_db_structure_names = [structure for structure in known_foundation_structure_names if structure not in db_structure_infos.keys()]

    if structure in db_structure_infos:
        color = db_structure_infos[structure][1]
    elif structure in non_db_structure_names:
        color = len(db_structure_infos) + non_db_structure_names.index(structure) + 1
    else:
        color = 255
    return color

def get_segment_properties(all_known=False):
    db_structure_infos = get_db_structure_infos()
    known_foundation_structure_names = get_known_foundation_structure_names()
    non_db_structure_names = [structure for structure in known_foundation_structure_names if structure not in db_structure_infos.keys()]

    segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
    if all_known:
        segment_properties += [(len(db_structure_infos) + index + 1, structure) for index, structure in enumerate(non_db_structure_names)]

    return segment_properties

def get_segment_ids(volume):
    ids = [int(i) for i in np.unique(volume[:])]
    segment_properties = [(number, f'{number}: {number}') for number in ids]
    return segment_properties

def get_hex_from_id(id, colormap='coolwarm'):
    cmap = cm.get_cmap(colormap, 255)
    rgba = cmap(id)
    return colors.rgb2hex(rgba)


class NumpyToNeuroglancer():
    viewer = None

    def __init__(self, volume, scales, layer_type, data_type, chunk_size=[256,256,128]):
        self.volume = volume
        self.scales = scales
        self.layer_type = layer_type
        self.data_type = data_type
        self.chunk_size = chunk_size
        self.precomputed_vol = None
        self.offset = [0, 0, 0]
        self.starting_points = None

    def init_precomputed(self, path, volume_size, starting_points=None, progress_dir=None):
        info = CloudVolume.create_new_info(
            num_channels=1,
            layer_type=self.layer_type,  # 'image' or 'segmentation'
            data_type=self.data_type,  #
            encoding='raw',  # other options: 'jpeg', 'compressed_segmentation' (req. uint32 or uint64)
            resolution=self.scales,  # Size of X,Y,Z pixels in nanometers,
            voxel_offset=self.offset,  # values X,Y,Z values in voxels
            chunk_size=self.chunk_size,  # rechunk of image X,Y,Z in voxels
            volume_size=volume_size,  # X,Y,Z size in voxels
        )
        self.starting_points = starting_points
        self.progress_dir = progress_dir
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=True, progress=False)
        self.precomputed_vol.commit_info()
        self.precomputed_vol.commit_provenance()

    def init_volume(self, path):
        info = CloudVolume.create_new_info(
            num_channels = self.volume.shape[3] if len(self.volume.shape) > 3 else 1,
            layer_type = self.layer_type,
            data_type = self.data_type, # str(self.volume.dtype),  # Channel images might be 'uint8'
            encoding = 'raw',  # raw, jpeg, compressed_segmentation, fpzip, kempressed
            resolution = self.scales,            # Voxel scaling, units are in nanometers
            voxel_offset = self.offset,          # x,y,z offset in voxels from the origin
            chunk_size = self.chunk_size,           # units are voxels
            volume_size = self.volume.shape[:3], # e.g. a cubic millimeter dataset
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=True, progress=False)
        self.precomputed_vol.commit_info()
        self.precomputed_vol[:, :, :] = self.volume[:, :, :]


    def add_segment_properties(self, segment_properties):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        self.precomputed_vol.info['segment_properties'] = 'names'
        self.precomputed_vol.commit_info()

        segment_properties_path = os.path.join(self.precomputed_vol.layer_cloudpath.replace('file://', ''), 'names')
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

    def add_downsampled_volumes(self, chunk_size=[128, 128, 64], num_mips=4):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')
        _, cpus = get_cpus()
        tq = LocalTaskQueue(parallel=cpus)
        tasks = tc.create_downsampling_tasks(self.precomputed_vol.layer_cloudpath, preserve_chunk_size=False,
                                             num_mips=num_mips, chunk_size=chunk_size, compress=True)
        tq.insert(tasks)
        tq.execute()

    def add_segmentation_mesh(self, shape=[448, 448, 448], mip=0):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        _, cpus = get_cpus()
        tq = LocalTaskQueue(parallel=cpus)
        tasks = tc.create_meshing_tasks(self.precomputed_vol.layer_cloudpath,mip=mip,
                                        max_simplification_error=40,
                                        shape=shape, compress=True) # The first phase of creating mesh
        tq.insert(tasks)
        tq.execute()
        # It should be able to incoporated to above tasks, but it will give a weird bug. Don't know the reason
        tasks = tc.create_mesh_manifest_tasks(self.precomputed_vol.layer_cloudpath) # The second phase of creating mesh
        tq.insert(tasks)
        tq.execute()


    def process_simple_slice(self, file_key):
        index, infile = file_key
        print(index, infile)
        try:
            image = Image.open(infile)
        except:
            print('Could not open', infile)
        width, height = image.size
        array = np.array(image, dtype=self.data_type, order='F')
        array = array.reshape((1, height, width)).T
        self.precomputed_vol[:,:, index] = array
        touchfile = os.path.join(self.progress_dir, os.path.basename(infile))
        touch(touchfile)
        image.close()
        return

    def process_mesh(self, file_key):
        index, infile = file_key
        if os.path.exists(os.path.join(self.progress_dir, os.path.basename(infile))):
            print(f"Section {index} already processed, skipping ")
            return
        img = io.imread(infile)
        img = img.T
        self.precomputed_vol[:, :, index] = img.reshape(img.shape[0], img.shape[1], 1)
        touchfile = os.path.join(self.progress_dir, os.path.basename(infile))
        touch(touchfile)
        del img
        return

    def process_coronal_slice(self, file_key):
        index, infile = file_key
        if os.path.exists(os.path.join(self.progress_dir, os.path.basename(infile))):
            print(f"Slice {index} already processed, skipping ")
            return

        img = io.imread(infile)
        starty, endy, startx, endx = self.starting_points
        #img = np.rot90(img, 2)
        #img = np.flip(img)
        img = img[starty:endy, startx:endx]
        img = img.reshape(img.shape[0], img.shape[1], 1)
        #print(index, infile, img.shape, img.dtype, self.precomputed_vol.dtype, self.precomputed_vol.shape)
        self.precomputed_vol[:, :, index] = img
        touchfile = os.path.join(self.progress_dir, os.path.basename(infile))
        touch(touchfile)
        del img
        return

    def process_image(self, file_key):
        index, infile = file_key
        if os.path.exists(os.path.join(self.progress_dir, os.path.basename(infile))):
            print(f"Section {index} already processed, skipping ")
            return
        img = io.imread(infile)
        img = img.reshape(1, img.shape[0], img.shape[1]).T
        self.precomputed_vol[:, :, index] = img
        touchfile = os.path.join(self.progress_dir, os.path.basename(infile))
        touch(touchfile)
        del img
        return

    def preview(self, layer_name=None, clear_layer=False):
        if self.viewer is None:
            self.viewer = neuroglancer.Viewer()

        if layer_name is None:
            layer_name = f'{self.layer_type}_{self.scales}'

        source = neuroglancer.LocalVolume(
            data=self.volume,
            dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='nm', scales=self.scales),
            voxel_offset=self.offset
        )

        if self.layer_type == 'segmentation':
            layer = neuroglancer.SegmentationLayer(source=source)
        else:
            layer = neuroglancer.ImageLayer(source=source)

        with self.viewer.txn() as s:
            if clear_layer:
                s.layers.clear()
            s.layers[layer_name] = layer

        print(f'A new layer named {layer_name} is added to:')
        print(self.viewer)


def mask_to_shell(mask):
    sub_contours = measure.find_contours(mask, 1)

    sub_shells = []
    for sub_contour in sub_contours:
        sub_contour.T[[0, 1]] = sub_contour.T[[1, 0]]
        pts = sub_contour.astype(np.int32).reshape((-1, 1, 2))
        sub_shell = np.zeros(mask.shape, dtype='uint8')
        sub_shell = cv2.polylines(sub_shell, [pts], True, 1, 5, lineType=cv2.LINE_AA)
        sub_shells.append(sub_shell)
    shell = np.array(sub_shells).sum(axis=0)
    del sub_shells
    return shell

