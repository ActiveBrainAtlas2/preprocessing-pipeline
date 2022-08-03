import sys
import os
sys.path.append(os.path.abspath('./pipeline'))
from atlas.FoundationContourAligner import FoundationContourAligner
from atlas.BrainStructureManager import BrainStructureManager
from atlas.VolumeMaker import VolumeMaker
from atlas.BrainMerger import BrainMerger
from atlas.NgSegmentMaker import AtlasNgMaker


def align_contour(animal):
    aligner = FoundationContourAligner(animal)
    aligner.create_aligned_contours()
    aligner.save_contours()


def create_volume(animal):
    brain = BrainStructureManager(animal)
    brain.load_aligned_contours()
    volumemaker = VolumeMaker()
    volumemaker.set_aligned_contours(brain.aligned_contours)
    volumemaker.compute_origins_and_volumes_for_all_segments()
    # volumemaker.save_coms()
    brain.origins,brain.volumes,brain.structures = volumemaker.origins,volumemaker.volumes,volumemaker.structures
    brain.save_origins()
    brain.save_volumes()


def merge_brains():
    merger = BrainMerger()
    merger.create_average_com_and_volume()
    # merger.save_mesh_files() 
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
