import sys
from pathlib import Path
PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from abakit.atlas.FoundationContourAligner import FoundationContourAligner
from abakit.atlas.VolumeMaker import VolumeMaker
from abakit.atlas.BrainMerger import BrainMerger
from abakit.atlas.NgSegmentMaker import AtlasNgMaker


def align_contour(animal):
    aligner = FoundationContourAligner(animal)
    aligner.create_aligned_contours()
    aligner.save_contours()


def create_volume(animal):
    volumemaker = VolumeMaker(animal)
    volumemaker.compute_COMs_origins_and_volumes()
    volumemaker.save_coms()
    volumemaker.save_origins()
    volumemaker.save_volumes()


def merge_brains():
    merger = BrainMerger()
    merger.create_average_com_and_volume()
    merger.save_mesh_files() 
    merger.save_origins() 

def make_ng_file():
    atlas = 'atlasV8'
    debug = False
    maker = AtlasNgMaker(atlas, debug, threshold=0.9)
    maker.assembler.assemble_all_structure_volume()
    maker.create_atlas_neuroglancer()


if __name__ == '__main__':
    animals = ['MD585', 'MD589', 'MD594']
    for animal in animals:
        align_contour(animal)
        create_volume(animal)
    merge_brains()
    make_ng_file()
