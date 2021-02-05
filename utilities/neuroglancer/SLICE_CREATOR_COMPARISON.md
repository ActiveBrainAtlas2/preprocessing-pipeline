### Comparison of different methods of creating a mesh volume
#### 1000 sections at 3456x2628 8-bit, data is gzipped compressed

1. Chunk size of 64
    1. Time to build: 24m24.429s  
    1. size of dir 1.1G
    1. loading: very slow
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_chunk_64 
1. Chunk size of 128
    1. Time to build:   23m43.315s
    1. size of dir: 918M
    1. loading: very slow
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_chunk_128
1. Chunk size of 256
    1. Time to build:   23m8.902s
    1. size of dir: 907M
    1. loading: very slow
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_chunk_256 
1. Chunk size of 512
    1. Time to build: 26m21.173s   
    1. size of dir: 900M
    1. loading: very slow
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_chunk_512
1. Chunk size of 1024
    1. Time to build: 30m31.084s  
    1. size of dir: 897M
    1. loading: very slow
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_chunk_1024 
### Notes
1. num_mips must be greater than 0, default is around 6
1. using the hybrid neuroglancer-scripts and igneuos gives same slow result at 3x3x3
1. seung: chunk_size=[512, 512, 16] when volume size is [250000, 250000, 25000], res: [4,4,40]
1. at 1um, our volume size is 10368x7885x13312
