from Brain import Brain
from atlas.BrainStructureManager import Atlas
from atlas.Assembler import AtlasAssembler
from atlas.VolumeUtilities import VolumeUtilities
from atlas.NgSegmentMaker import AtlasNgMaker
import numpy as np
class CustomAtlasVolumeMaker(Brain):
    def __init__(self,animal,atlas = 'atlasV8',volume_threshold = 0.9,sigma = 3):
        super().__init__(animal)
        self.assembler = AtlasAssembler(atlas,com_function = self.get_com)
        self.ng_maker = AtlasNgMaker(atlas,out_folder = f'{animal} manual')
    
    def get_com(self):
        self.load_com()
        return self.COM

if __name__ == '__main__':
    maker = CustomAtlasVolumeMaker('DK52')
    maker.assembler.assemble_all_structure_volume()
    volume = maker.assembler.combined_volume
    maker.ng_maker.create_neuroglancer_files(volume)
    maker.plotter.plot_3d_image_stack(volume,2)