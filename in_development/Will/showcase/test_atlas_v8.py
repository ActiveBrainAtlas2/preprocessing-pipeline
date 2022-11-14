from atlas.NgSegmentMaker import AtlasNgMaker
atlas = 'atlasV8'
debug = False
maker = AtlasNgMaker(atlas, debug, threshold=0.9,atlas_folder = 'v8reconstruct')
maker.assembler.assemble_all_structure_volume()
maker.create_atlas_neuroglancer()