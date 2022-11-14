import os
from skimage import measure, io
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import cv2
import json
import numpy as np
import neuroglancer
from taskqueue import LocalTaskQueue
import igneous.task_creation as tc
from cloudvolume import CloudVolume
from cloudvolume.lib import touch
from matplotlib import colors
from pylab import cm
from collections import defaultdict
from controller.sql_controller import SqlController
from utilities.utilities_process import get_cpus


def calculate_chunks(downsample, mip):
    '''Function returns chunk sizes for different 'precomputed cloud volume' image stack resolutions

    Image stack will be created from full-resolution images but must be chunked for efficient storage and loading into browser.
    Default values are [64, 64, 64] but may be modified for different resolutions.
    More info: https://github.com/seung-lab/cloud-volume

    Note: highest resolution tier (mip)  is 0 and increments

    :param downsample:
    :type downsample:
    :param mip:
    :type mip:
    :return:
    :rtype:
    '''
    d = defaultdict(dict)
    result = [64, 64, 64]
    d[False][-1] = [1024, 1024, 1]
    d[False][0] = [256, 256, 128]
    d[False][1] = [128, 128, 64]
    d[False][2] = [128, 128, 64]
    d[False][3] = [128, 128, 64]
    d[False][4] = [128, 128, 64]
    d[False][5] = [64, 64, 64]
    d[False][6] = [64, 64, 64]
    d[False][7] = [64, 64, 64]
    d[False][8] = [64, 64, 64]
    d[False][9] = [64, 64, 64]

    d[True][-1] = [64, 64, 1]
    d[True][0] = [64, 64, 64]
    d[True][1] = [64, 64, 64]
    d[True][2] = [64, 64, 32]
    d[True][3] = [32, 32, 16]

    try:
        result = d[downsample][mip]
    except:
        result = [64,64,64]
    return result


def calculate_factors(downsample, mip):
    '''Scales get calculated by default by 2x2x1 downsampling

    :param downsample:
    :type downsample:
    :param mip:
    :type mip:
    :return:
    :rtype:
    '''
    d = defaultdict(dict)
    result = [2,2,1]
    d[False][0] = result
    d[False][1] = result
    d[False][2] = result
    d[False][3] = result
    d[False][4] = result
    d[False][5] = result
    d[False][6] = result
    d[False][7] = [2,2,2]
    d[False][8] = [2,2,2]
    d[False][9] = [2,2,2]

    d[True][0] = [2,2,1]
    d[True][1] = [2,2,1]
    d[True][2] = [2,2,1]
    d[True][3] = [2,2,1]
    try:
        result = d[downsample][mip]
    except:
        result = [2,2,1]
    return result


def get_db_structure_infos():
    '''Unknown - Needs more info [possibly just for testing and may be removed]
    Comment based on hard-coded 'MD589'

    :return:
    :rtype:
    '''
    sqlController = SqlController('MD589')
    db_structures = sqlController.get_structures_dict()
    structures = {}
    for structure, v in db_structures.items():
        if '_' in structure:
            structure = structure[0:-2]
        structures[structure] = v
    return structures


def get_known_foundation_structure_names() -> list[str]:
    '''Unknown - Needs more info [possibly just for testing and may be removed]
    Comment based on presence of these same structure names in database (not static) but, if required,
    should be moved to static variable declaration (lookup tables)

    :return:
    :rtype:
    '''
    known_foundation_structures = ['MVePC', 'DTgP', 'VTA', 'Li', 'Op', 'Sp5C', 'RPC', 'MVeMC', 'APT', 'IPR',
                                   'Cb', 'pc', 'Amb', 'SolIM', 'Pr5VL', 'IPC', '8n', 'MPB', 'Pr5', 'SNR',
                                   'DRD', 'PBG', '10N', 'VTg', 'R', 'IF', 'RR', 'LDTg', '5TT', 'Bar',
                                   'Tz', 'IO', 'Cu', 'SuVe', '12N', '6N', 'PTg', 'Sp5I', 'SNC', 'MnR',
                                   'RtTg', 'Gr', 'ECu', 'DTgC', '4N', 'IPA', '3N', '7N', 'LC', '7n',
                                   'SC', 'LPB', 'EW', 'Pr5DM', 'VCA', '5N', 'Dk', 'DTg', 'LVe', 'SpVe',
                                   'MVe', 'LSO', 'InC', 'IC', 'Sp5O', 'DC', 'Pn', 'LRt', 'RMC', 'PF',
                                   'VCP', 'CnF', 'Sol', 'IPL', 'X', 'AP', 'MiTg', 'DRI', 'RPF', 'VLL']
    return known_foundation_structures


def get_structure_number(structure: str) -> str:
    '''Unknown - Needs more info [possibly just for testing and may be removed]
    Likely deprecated as we do not use 'color' attribute of brains and call to get_db_structure_infos(), which has hard-coded 'MD589'

    :param structure:
    :type structure: str
    :return:
    :rtype: str
    '''
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


def get_segment_properties(all_known: bool = False):
    '''Unknown - Needs more info [possibly just for testing and may be removed]
    Comment based on call to get_db_structure_infos(), which has hard-coded 'MD589'

    :param all_known:
    :type all_known:
    :return:
    :rtype:
    '''
    db_structure_infos = get_db_structure_infos()
    known_foundation_structure_names = get_known_foundation_structure_names()
    non_db_structure_names = [structure for structure in known_foundation_structure_names if structure not in db_structure_infos.keys()]

    segment_properties = [(number, f'{structure}: {label}') for structure, (label, number) in db_structure_infos.items()]
    if all_known:
        segment_properties += [(len(db_structure_infos) + index + 1, structure) for index, structure in enumerate(non_db_structure_names)]

    return segment_properties


def get_segment_ids(volume):
    '''Unknown - Needs more info

    :param volume:
    :type volume:
    :return:
    :rtype:
    '''
    ids = [int(i) for i in np.unique(volume[:])]
    segment_properties = [(number, f'{number}: {number}') for number in ids]
    return segment_properties


def get_hex_from_id(id, colormap: str = 'coolwarm'):
    '''Unknown - Needs more info [possibly just for testing and may be removed]
    Likely deprecated as we do not use 'color' attribute of brains

    :param id:
    :type id:
    :param colormap: str
    :type colormap:
    :return:
    :rtype:
    '''
    cmap = cm.get_cmap(colormap, 255)
    rgba = cmap(id)
    return colors.rgb2hex(rgba)


class NumpyToNeuroglancer():
    '''Contains collection of methods used to transform Numpy arrays into 'precomputed cloud volume' format
    More info: https://github.com/seung-lab/cloud-volume

    Methods
    -------
    __init__()
    init_precomputed()
    init_volume()
    add_segment_properties()
    add_rechunking()
    add_downsampled_volumes()
    add_segmentation_mesh()
    process_simple_slice()
    process_mesh()
    process_coronal_slice()
    process_image()
    get_dimensions()
    add_annotation_layer()
    add_annotation_point_set()
    add_annotation_point()
    clear_layer()
    add_layer()
    init_layer()
    report_new_layer()
    add_volume()
    preview()

    '''
    viewer = None

    def __init__(self, animal: str, volume, scales, layer_type, data_type, num_channels=1,
        chunk_size: list[int] = [256,256,128], offset: list[int] = [0,0,0]):
        self.volume = volume
        self.scales = scales
        self.layer_type = layer_type
        self.data_type = data_type
        self.chunk_size = chunk_size
        self.precomputed_vol = None
        self.offset = offset
        self.starting_points = None
        self.animal = animal
        self.num_channels = num_channels


    def init_precomputed(self, path: str, volume_size, starting_points=None, progress_id=None) -> None:
        '''Initializes 'precomputed' cloud volume format (directory holding multiple volumes)

        :param path:
        :type path: str
        :param volume_size:
        :type volume_size:
        :param starting_points:
        :type starting_points:
        :param progress_id:
        :type progress_id:
        :return:
        :rtype:
        '''
        info = CloudVolume.create_new_info(
            num_channels=self.num_channels,
            layer_type=self.layer_type,  # 'image' or 'segmentation'
            data_type=self.data_type,  #
            encoding='raw',  # other options: 'jpeg', 'compressed_segmentation' (req. uint32 or uint64)
            resolution=self.scales,  # Size of X,Y,Z pixels in nanometers,
            voxel_offset=self.offset,  # values X,Y,Z values in voxels
            chunk_size=self.chunk_size,  # rechunk of image X,Y,Z in voxels
            volume_size=volume_size,  # X,Y,Z size in voxels
        )
        self.starting_points = starting_points
        self.progress_id = progress_id
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=True, progress=False)
        self.precomputed_vol.commit_info()
        self.precomputed_vol.commit_provenance()


    def init_volume(self, path: str) -> None:
        '''Initializes 'precomputed' cloud volume ('volume' is a collection image stack with same resolution)

        :param path:
        :type path: str
        :return:
        :rtype:
        '''
        info = CloudVolume.create_new_info(
            num_channels = self.volume.shape[2] if len(self.volume.shape) > 2 else 1,
            layer_type = self.layer_type,
            data_type = self.data_type, # str(self.volume.dtype),  # Channel images might be 'uint8'
            encoding = 'raw',  # raw, jpeg, compressed_segmentation, fpzip, kempressed
            resolution = self.scales,            # Voxel scaling, units are in nanometers
            voxel_offset = self.offset,          # x,y,z offset in voxels from the origin
            chunk_size = self.chunk_size,           # units are voxels
            volume_size = self.volume.shape[:3], # e.g. a cubic millimeter dataset
        )
        self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=True, progress=False)
        self.precomputed_vol[:, :, :] = self.volume[:, :, :]
        self.precomputed_vol.commit_info()
        self.precomputed_vol.commit_provenance()


    def add_segment_properties(self, segment_properties) -> None:
        '''Augments 'precomputed' cloud volume with attribute tags [resolution, chunk size]

        :param segment_properties:
        :type segment_properties:
        :return:
        :rtype:
        '''
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


    def add_rechunking(self, outpath: str, downsample, chunks=None) -> None:
        '''Augments 'precomputed' cloud volume with additional chunk calculations
        [so format has pointers to location of individual volumes?]

        :param outpath:
        :type outpath: str
        :param downsample:
        :type downsample:
        :param chunks:
        :type chunks:
        :return:
        :rtype:
        '''
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')
        cpus, _ = get_cpus()
        tq = LocalTaskQueue(parallel=cpus)
        outpath = f'file://{outpath}'
        if chunks is None:
            chunks = calculate_chunks(downsample, 0)
        tasks = tc.create_transfer_tasks(self.precomputed_vol.layer_cloudpath, 
            dest_layer_path=outpath, chunk_size=chunks, skip_downsamples=True)
        tq.insert(tasks)
        tq.execute()


    def add_downsampled_volumes(self, chunk_size: list[int] = [128, 128, 64], num_mips: int = 4) -> None:
        '''Augments 'precomputed' cloud volume with additional resolutions using chunk calculations

        :param chunk_size:
        :type chunk_size: list[int]
        :param num_mips:
        :type num_mips: int
        :return:
        :rtype:
        '''
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')
        _, cpus = get_cpus()
        tq = LocalTaskQueue(parallel=cpus)
        tasks = tc.create_downsampling_tasks(self.precomputed_vol.layer_cloudpath, preserve_chunk_size=False,
                                             num_mips=num_mips, chunk_size=chunk_size, compress=True)
        tq.insert(tasks)
        tq.execute()


    def add_segmentation_mesh(self, shape: list[int] = [448, 448, 448], mip: int = 0) -> None:
        '''Augments 'precomputed' cloud volume with segmentation mesh

        :param shape:
        :type shape: list[int]
        :param mip:
        :type mip: int
        :return:
        :rtype:
        '''
        if self.precomputed_vol is None:
            raise NotImplementedError('You have to call init_precomputed before calling this function.')

        _, cpus = get_cpus()
        tq = LocalTaskQueue(parallel=cpus)
        tasks = tc.create_meshing_tasks(self.precomputed_vol.layer_cloudpath,mip=mip,
                                        max_simplification_error=40,
                                        shape=shape, compress=True) # The first phase of creating mesh
        tq.insert(tasks)
        tq.execute()
        # It should be able to incorporate to above tasks, but it will give a weird bug. Don't know the reason
        tasks = tc.create_mesh_manifest_tasks(self.precomputed_vol.layer_cloudpath) # The second phase of creating mesh
        tq.insert(tasks)
        tq.execute()


    def process_simple_slice(self, file_key):
        '''Unknown role but method a)loops through image stack, b) loads into Numpy array, c) reshapes in single dimension,
        d) adds to 'precomputed' cloud volume, e) touches files to track progress

        :param file_key:
        :type file_key:
        :return:
        :rtype:
        '''
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
        '''Unknown role but method a) loops through image stack, b) loads into Numpy array, c) applies mask?
        d) transposes Numpy array, e) adds to 'precomputed' cloud volume

        Unclear where values for labels range came from

        :param file_key:
        :type file_key:
        :return:
        :rtype:
        '''
        index, infile = file_key
        if os.path.exists(os.path.join(self.progress_dir, os.path.basename(infile))):
            print(f"Section {index} already processed, skipping ")
            return
        img = io.imread(infile)
        labels = [[v-8,v-1] for v in range(9,256,8)]
        arr = np.copy(img)
        for label in labels:
            mask = (arr >= label[0]) & (arr <= label[1])
            arr[mask] = label[1]
        arr[arr > 248] = 255        
        img = arr.T
        del arr
        self.precomputed_vol[:, :, index] = img.reshape(img.shape[0], img.shape[1], 1)
        touchfile = os.path.join(self.progress_dir, os.path.basename(infile))
        touch(touchfile)
        del img
        return


    def process_coronal_slice(self, file_key):
        '''Unknown role but method a) loops through image stack, b) loads into Numpy array, c) reshapes each image
        d) adds to 'precomputed' cloud volume

        Only for coronal-sliced brains?

        :param file_key:
        :type file_key:
        :return:
        :rtype:
        '''
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
        '''Unknown role but method a) reads single file, b) reshapes/transforms, c) adds to 'precomputed' cloud volume

        :param file_key:
        :type file_key:
        :return:
        :rtype:
        '''
        index, infile, orientation, progress_dir = file_key
        basefile = os.path.basename(infile)
        progress_file = os.path.join(progress_dir, basefile)
        if os.path.exists(progress_file):
             print(f"Section {index} has already been processed, skipping.")
             return

        try:
            img = io.imread(infile, img_num=0)
        except IOError as ioe:
            print(f'could not open {infile} {ioe}')
            return
        try:
            img = img.reshape(self.num_channels, img.shape[0], img.shape[1]).T
        except:
            print(f'could not reshape {infile}')
            return
        try:
            self.precomputed_vol[:, :, index] = img
        except:
            print(f'could not set {infile} to precomputed')
            return

        touch(progress_file)
        del img
        return


    def get_dimensions(self):
        '''Unknown - Needs more info

        :return:
        :rtype:
        '''
        return neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='nm', scales=self.scales)


    def add_annotation_layer(self, layer_name, annotations) -> None:
        '''Unknown - Needs more info

        adds annotation layer? If so, not part of preprocessing-pipeline

        :param layer_name:
        :type layer_name:
        :param annotations:
        :type annotations:
        :return:
        :rtype:
        '''
        dimensions = self.get_dimensions()
        with self.viewer.txn() as s:
            s.layers.append(name=layer_name,
                    layer=neuroglancer.LocalAnnotationLayer(dimensions=dimensions,
                    annotations=annotations))


    def add_annotation_point_set(self, cooridnate_list, point_id_list = None, layer_name=None, clear_layer: bool = False) -> None:
        '''Unknown - Needs more info

        adds coordinate points to annotation layer to Neuroglancer? If so, not part of preprocessing-pipeline

        :param cooridnate_list:
        :type cooridnate_list:
        :param point_id_list:
        :type point_id_list:
        :param layer_name:
        :type layer_name:
        :param clear_layer:
        :type clear_layer:
        :return:
        :rtype:
        '''
        n_annotations = len(cooridnate_list)
        if point_id_list == None:
            point_id_list = [str(elementi) for elementi in list(range(n_annotations))]
        self.init_layer(clear_layer)
        annotations = []
        for annotationi in range(n_annotations):
            point_annotation = neuroglancer.PointAnnotation(id=point_id_list[annotationi],point=cooridnate_list[annotationi])
            annotations.append(point_annotation)
        self.add_annotation_layer(layer_name,annotations)
        self.report_new_layer(layer_name)


    def add_annotation_point(self, cooridnate, point_id='pointi', layer_name=None, clear_layer: bool = False) -> None:
        '''Unknown - Needs more info

        adds single coordinate point to annotation layer to Neuroglancer? If so, not part of preprocessing-pipeline

        :param cooridnate:
        :type cooridnate:
        :param point_id:
        :type point_id:
        :param layer_name:
        :type layer_name:
        :param clear_layer:
        :type clear_layer:
        :return:
        :rtype:
        '''
        self.init_layer(clear_layer)
        annotations=[neuroglancer.PointAnnotation(id=point_id,point=cooridnate)]
        self.add_annotation_layer(layer_name,annotations)
        self.report_new_layer(layer_name)


    def clear_layer(self, clear_layer: bool = False) -> None:
        '''Unknown - Needs more info

        removes annotation layer from Neuroglancer? If so, not part of preprocessing-pipeline

        :param clear_layer:
        :type clear_layer: bool
        :return:
        :rtype:
        '''
        if clear_layer:
            with self.viewer.txn() as s:
                    s.layers.clear()


    def add_layer(self, layer_name: str, layer) -> None:
        '''Unknown - Needs more info

        adds annotation layer to Neuroglancer? If so, not part of preprocessing-pipeline

        :param layer_name:
        :type layer_name: str
        :param layer:
        :type layer:
        :return:
        :rtype:
        '''
        with self.viewer.txn() as s:
            s.layers[layer_name] = layer
    
    def init_layer(self, clear_layer) -> None:
        '''Unknown - Needs more info

        initializes [image or annotation] layer for Neuroglancer? If so, not part of preprocessing-pipeline

        :param clear_layer:
        :type clear_layer:
        :return:
        :rtype:
        '''
        if self.viewer is None:
            self.viewer = neuroglancer.Viewer()
        self.clear_layer(clear_layer)


    def report_new_layer(self, layer_name: str) -> None:
        '''Appears to be for debugging; REMOVE

        :param layer_name:
        :type layer_name:
        :return:
        :rtype:
        '''
        print(f'A new layer named {layer_name} is added to:')
        print(self.viewer)


    def add_volume(self, volume, layer_name: str = None, clear_layer: bool = False) -> None:
        '''Unknown - Needs more info

        adds volume to precomputed cloud volume format?

        :param volume:
        :type volume:
        :param layer_name:
        :type layer_name:
        :param clear_layer:
        :type clear_layer:
        :return:
        :rtype:
        '''
        self.init_layer(clear_layer)
        if layer_name is None:
            layer_name = f'{self.layer_type}_{self.scales}'
        source = neuroglancer.LocalVolume(
            data=volume,
            dimensions=neuroglancer.CoordinateSpace(names=['x', 'y', 'z'], units='nm', scales=self.scales),
            voxel_offset=self.offset)
        if self.layer_type == 'segmentation':
            layer = neuroglancer.SegmentationLayer(source=source)
        else:
            layer = neuroglancer.ImageLayer(source=source)
        self.add_layer(layer_name,layer)
        self.report_new_layer(layer_name)


    def preview(self, layer_name: str = None, clear_layer: bool = False) -> None:
        '''Unknown - Needs more info

        adds volume to precomputed cloud volume format? Name inconsistent with function

        :param layer_name:
        :type layer_name:
        :param clear_layer:
        :type clear_layer:
        :return:
        :rtype:
        '''
        self.add_volume(self.volume,layer_name=layer_name, clear_layer=clear_layer)


def mask_to_shell(mask):
    '''Unknown - Needs more info

    :param mask:
    :type mask:
    :return:
    :rtype:
    '''
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