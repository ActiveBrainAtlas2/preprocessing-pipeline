from Brain import Brain
from atlas.Atlas import Atlas
from atlas.Assembler import AtlasAssembler
from atlas.VolumeUtilities import VolumeUtilities
from atlas.NgSegmentMaker import AtlasNgMaker
from lib.SqlController import SqlController
import numpy as np
class CustomAtlasVolumeMaker(Brain):
    def __init__(self,animal,atlas = 'atlasV8',volume_threshold = 0.9,sigma = 3):
        super().__init__(animal)
        self.assembler = AtlasAssembler(atlas,com_function = self.get_com,conversion_factor = self.um_to_pixel)
        self.ng_maker = AtlasNgMaker(atlas,out_folder = f'{animal} manual',offset = [360,-166,-227])
    
    def get_com(self):
        self.load_com()
        return self.COM

if __name__ == '__main__':
    controller = SqlController('DK52')
    animals = controller.get_annotated_animals()
    animals = [i for i in animals if 'DK' in i]
    for animali in animals:
        print(animali)
        maker = CustomAtlasVolumeMaker(animali)
        maker.assembler.assemble_all_structure_volume()
        volume = maker.assembler.combined_volume
        maker.ng_maker.create_neuroglancer_files(volume)
    # maker.plotter.plot_3d_image_stack(volume,2)