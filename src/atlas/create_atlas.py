from atlas.FundationContourAligner import FundationContourAligner
from atlas.VolumeMaker import VolumeMaker
from atlas.BrainMerger import BrainMerger
from atlas.NgSegmentMaker import AtlasNgMaker

def align_contour(animali):
    aligner = FundationContourAligner(animal)
    aligner.create_aligned_contours()
    aligner.save_contours()

def create_volume(animali):
    volumemaker = VolumeMaker(animal)
    volumemaker.compute_COMs_origins_and_volumes()
    volumemaker.save_coms()
    volumemaker.save_origins()
    volumemaker.save_volumes()

def merge_brains():
    merger = BrainMerger()
    merger.create_average_com_and_volume()
    merger.save_mesh_file()
    merger.save_origins()
    merger.save_coms()

def make_ng_file():
    atlas = 'atlasV8'
    debug = False
    maker = AtlasNgMaker(atlas,debug,threshold=0.9)
    maker.assembler.assemble_all_structure_volume()
    maker.create_atlas_neuroglancer()

if __name__ == '__main__':
    animals = ['MD585', 'MD589', 'MD594']
    for animal in animals:
        align_contour(animal)
        create_volume(animal)

    merge_brains()
    make_ng_file()