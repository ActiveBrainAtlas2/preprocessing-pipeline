import sys
from pathlib import Path

PIPELINE_ROOT = Path('./src').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())


from ng_segment_maker import AtlasNgMaker


def make_ng_file():
    atlas = 'atlasV8'
    debug = False
    maker = AtlasNgMaker(atlas, debug, threshold=0.9)
    maker.assembler.assemble_all_structure_volume()
    #maker.create_atlas_neuroglancer()


if __name__ == '__main__':
    make_ng_file()
    