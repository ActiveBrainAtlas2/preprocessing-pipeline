from atlas.Assembler import Assembler
from atlas.atlas_manager import Atlas
from atlas.NgSegmentMaker import NgSegmentMaker
class AtlasV7Builder(Atlas,Assembler,NgSegmentMaker):
    def __init__(self,debug = False,out_folder = 'rebuild_atlas7',threshold = 0.9,sigma = 3.0,offset = None):
        Atlas.__init__(self,'atlasV7')
        self.load_volumes()
        self.load_com()
        self.convert_unit_of_com_dictionary(self.COM, self.fixed_brain.um_to_pixel)
        self.origins = self.get_origin_from_coms()
        Assembler.__init__(self)
        NgSegmentMaker.__init__(self, debug,out_folder=out_folder,offset=offset)
        self.resolution = self.get_atlas_resolution()
        self.scales = [self.resolution,self.resolution,20* 32 * 1000]


if __name__ == '__main__':
    builder = AtlasV7Builder()
    builder.assemble_all_structure_volume()
    builder.volume = builder.combined_volume
    segment_properties = builder.get_segment_properties()
    builder.create_neuroglancer_files(builder.OUTPUT_DIR,segment_properties)