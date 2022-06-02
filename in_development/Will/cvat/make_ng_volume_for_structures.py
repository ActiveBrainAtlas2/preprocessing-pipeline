from abakit.atlas.BrainStructureManager import BrainStructureManager
from abakit.atlas.VolumeMaker import VolumeMaker
from abakit.atlas.Assembler import BrainAssembler
from abakit.atlas.NgSegmentMaker import BrainNgMaker
import numpy as np

def find_average_of_two_masks(mask1,mask2):
    d1 = distance_transform_edt(mask1) - distance_transform_edt(np.logical_not(mask1))
    d2 = distance_transform_edt(mask2) - distance_transform_edt(np.logical_not(mask2))
    return (d1+d2)>0

def interpolate_volume(volume,niter = 3):
    for _ in range(niter):
        volume = interpolate_once(volume)

def interpolate_once(volume):
    xdim,ydim,zdim = volume.shape
    interpolated_volume = np.zeros([xdim,ydim,2*zdim-1])
    for zi in range(zdim):
        interpolated_volume[:,:,2*zi] = volume[:,:,zi]
        if not zi == zdim-1:
            interpolated_volume[:,:,2*zi+1] = find_average_of_two_masks(volume[:,:,zi],volume[:,:,zi+1])
    return interpolated_volume

def make_volumes():
    vmaker = VolumeMaker('DK55',downsample_factor=8)
    xml_path = '/home/zhw272/Downloads/annotations.xml'
    contours = vmaker.load_contours_from_cvat_xml(xml_path)
    contours['SpV_L'] = contours['Trigeminal']
    del contours['Trigeminal']
    vmaker.set_aligned_contours(contours)
    vmaker.compute_COMs_origins_and_volumes()
    vmaker.save_origins()
    vmaker.save_volumes()
    assembler = BrainAssembler('DK55',threshold=0.8,downsample_factor=8)
    assembler.origins['SpV_L'] = np.array([0,0,0])
    assembler.volumes['SpV_L'] = assembler.volumes['SpV_L']
    assembler.assemble_all_structure_volume()
    offset = vmaker.origins['SpV_L']
    # offset = [10,10,10]
    maker = BrainNgMaker(animal = 'DK55',out_folder='DK55_trigeminal_test',offset = list(offset))
    maker.resolution = 2600
    maker.create_neuroglancer_files(assembler.combined_volume)


make_volumes()


