from atlas.BrainStructureManager import BrainStructureManager
from atlas.VolumeMaker import VolumeMaker
from atlas.Assembler import BrainAssembler
from atlas.NgSegmentMaker import BrainNgMaker
import numpy as np
def make_volumes():
    maker = VolumeMaker('DK55',downsample_factor=8)
    xml_path = '/home/zhw272/Downloads/annotations.xml'
    contours = maker.load_contours_from_cvat_xml(xml_path)
    contours['SpV_L'] = contours['Trigeminal']
    del contours['Trigeminal']
    maker.set_aligned_contours(contours)
    maker.compute_COMs_origins_and_volumes()
    maker.save_origins()
    maker.save_volumes()


make_volumes()
assembler = BrainAssembler('DK55',threshold=0.8,downsample_factor=8)
assembler.origins['SpV_L'] = np.array([0,0,0])
assembler.assemble_all_structure_volume()
# assembler.plotter.plot_3d_image_stack(assembler.combined_volume,axis=2) 
maker = BrainNgMaker(animal = 'DK55',out_folder='DK55_trigeminal',offset = [0,0,0])
maker.resolution = 0.325
maker.create_neuroglancer_files(assembler.combined_volume)


breakpoint()