from abakit.atlas.BrainStructureManager import BrainStructureManager
from abakit.atlas.VolumeMaker import VolumeMaker
from abakit.atlas.Assembler import BrainAssembler
from abakit.atlas.NgSegmentMaker import BrainNgMaker
import numpy as np
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
    assembler.assemble_all_structure_volume()
    # assembler.plotter.plot_3d_image_stack(assembler.combined_volume,axis=2) 
    offset = vmaker.origins['SpV_L']
    # offset = [10,10,10]
    maker = BrainNgMaker(animal = 'DK55',out_folder='DK55_trigeminal_test',offset = list(offset))
    maker.resolution = 2600
    maker.create_neuroglancer_files(assembler.combined_volume)


make_volumes()


breakpoint()