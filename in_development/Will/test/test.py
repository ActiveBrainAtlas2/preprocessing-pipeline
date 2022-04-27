from abakit.atlas.Assembler import AtlasAssembler

assembler = AtlasAssembler('atlasV7', threshold=0.01,sigma = 1)
assembler.assemble_all_structure_volume()