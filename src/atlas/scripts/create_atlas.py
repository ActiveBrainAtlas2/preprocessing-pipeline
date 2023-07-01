from foundation_contour_aligner import FoundationContourAligner
from brain_structure_manager import BrainStructureManager
from volume_maker import VolumeMaker
from brain_merger import BrainMerger
from ng_segment_maker import AtlasNgMaker


def align_contour(animal):
    aligner = FoundationContourAligner(animal)
    aligner.create_aligned_contours()
    aligner.save_contours()


def create_volume(animal):
    brain = BrainStructureManager(animal)
    brain.load_aligned_contours()
    volumemaker = VolumeMaker()
    volumemaker.set_aligned_contours(brain.aligned_contours)
    return
    volumemaker.compute_origins_and_volumes_for_all_segments()
    brain.save_coms()
    brain.origins = volumemaker.origins
    brain.volumes = volumemaker.volumes
    brain.structures = volumemaker.structures
    print(f'len origins={len(brain.origins)}')
    print(f'len volumes={len(brain.volumes)} and type={type(brain.volumes)}')
    print(f'len structures={len(brain.structures)}')
    brain.save_origins()
    brain.save_volumes()


def merge_brains():
    merger = BrainMerger()
    merger.create_average_com_and_volume()
    #merger.save_mesh_files() 
    merger.save_origins_and_volumes()

def make_ng_file():
    atlas = 'atlasV8'
    debug = False
    maker = AtlasNgMaker(atlas, debug, threshold=0.9)
    maker.assembler.assemble_all_structure_volume()
    maker.create_atlas_neuroglancer()


if __name__ == '__main__':
    animals = ['MD585', 'MD589', 'MD594']
    for animal in animals:
        print(f'Working on {animal}')
        #align_contour(animal)
        #create_volume(animal)
    merge_brains()
    #make_ng_file()
