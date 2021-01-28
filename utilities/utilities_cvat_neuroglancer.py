import os
import sys
from skimage import measure
import cv2
import json
import socket

import numpy as np
import neuroglancer
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
from pathlib import Path
from skimage import io
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())


def get_cpus():
    usecpus = 3
    cpus = {}
    cpus['muralis'] = 25
    cpus['basalis'] = 10
    cpus['ratto'] = 10
    hostname = socket.gethostname()
    hostname = hostname.split(".")[0]
    if hostname in cpus.keys():
        usecpus = cpus[hostname]
    return usecpus


from utilities.sqlcontroller import SqlController

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



class NumpyToNeuroglancer():
    viewer = None

    def __init__(self, volume, scales, layer_type, data_type, chunk_size):
        self.volume = volume
        self.scales = scales
        self.layer_type = layer_type
        self.data_type = data_type
        self.chunk_size = chunk_size
        self.precomputed_vol = None
        self.offset = [0, 0, 0]

    def init_precomputed(self, path, volume_size):
        info = CloudVolume.create_new_info(
            num_channels=1,
            layer_type=self.layer_type,  # 'image' or 'segmentation'
            data_type=self.data_type,  #
            encoding='raw',  # other options: 'jpeg', 'compressed_segmentation' (req. uint32 or uint64)
            resolution=self.scales,  # Size of X,Y,Z pixels in nanometers,
            voxel_offset=self.offset,  # values X,Y,Z values in voxels
            chunk_size=self.chunk_size,  # rechunk of image X,Y,Z in voxels -- only used for downsampling task I think
            volume_size=volume_size,  # X,Y,Z size in voxels
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=False, progress=False)
        self.precomputed_vol.commit_info()

    def init_volume(self, path):
        info = CloudVolume.create_new_info(
            num_channels = self.volume.shape[3] if len(self.volume.shape) > 3 else 1,
            layer_type = self.layer_type,
            data_type = str(self.volume.dtype),  # Channel images might be 'uint8'
            encoding = 'raw',                    # raw, jpeg, compressed_segmentation, fpzip, kempressed
            resolution = self.scales,            # Voxel scaling, units are in nanometers
            voxel_offset = self.offset,          # x,y,z offset in voxels from the origin
            chunk_size = self.chunk_size,           # units are voxels
            volume_size = self.volume.shape[:3], # e.g. a cubic millimeter dataset
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=False, progress=False)
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

    def add_downsampled_volumes(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')
        cpus = get_cpus()
        tq = LocalTaskQueue(parallel=cpus)
        tasks = tc.create_downsampling_tasks(self.precomputed_vol.layer_cloudpath, num_mips=4, preserve_chunk_size=False, compress=False)
        tq.insert(tasks)
        tq.execute()

    def add_segmentation_mesh(self):
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        cpus = get_cpus()
        tq = LocalTaskQueue(parallel=cpus)
        tasks = tc.create_meshing_tasks(self.precomputed_vol.layer_cloudpath, mip=0, compress=False) # The first phase of creating mesh
        tq.insert(tasks)
        tq.execute()
        # It should be able to incoporated to above tasks, but it will give a weird bug. Don't know the reason
        tasks = tc.create_mesh_manifest_tasks(self.precomputed_vol.layer_cloudpath) # The second phase of creating mesh
        tq.insert(tasks)
        tq.execute()


    def process_slice(self, file_key):
        index, infile = file_key
        image = Image.open(infile)
        width, height = image.size
        array = np.array(image, dtype=self.data_type, order='F')
        array = array.reshape((1, height, width)).T
        self.precomputed_vol[:, :, index] = array
        print(infile, array.shape)
        image.close()
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

