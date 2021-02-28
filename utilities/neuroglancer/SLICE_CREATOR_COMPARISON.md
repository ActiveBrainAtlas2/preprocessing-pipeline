### Comparison of different methods of creating a mesh volume
#### 8-bit, data is gzipped compressed

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
1. Chunk size of 64,64,64
    1. sections: 200
    1. loading: ok
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal 
1. Chunk size of 64,64,64 @ 1x1x1
    1. sections: 1000
    1. loading: slow and stalled at 192/556
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal 
1. Chunk size of 64,64,64
    1. Time to build: 56m22.163s
    1. dir size: 1.4GB   
    1. sections: 200
    1. loading: slow but completed
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal_nocompress 
1. Chunk size of 128,128,128
    1. Time to build: real	85m27.526s
    1. sections: 500
    1. loading: stalled at 264/369
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal
1. Chunk size of 64,64,16
    1. Time to build: 93m19.556s
    1. sections: 500
    1. loading: stalled at 264/369
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal
1. Chunk size of 256, 256, 32
    1. dir size: 391MB
    1. Time to build: 58m3.246s
    1. sections: 200
    1. loading: ok completed 187/187
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal_256_256_32
1. Chunk size of 1024x1024x32
    1. dir size: 
    1. Time to build: 
    1. sections: 1000
    1. loading: 
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal_1024x1024x32
1. Chunk size of 512x512x32
    1. dir size: 2.2GB
    1. Time to build: 75m47.984s
    1. sections: 3500x2600x3000
    1. loading: stalled at 156/335
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_half_half
1. Chunk size of 1024x1024x32
    1. dir size: 1.8GB
    1. Time to build: 131m9.852s
    1. sections: 1000
    1. loading: stalled at 192/556
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal_1024x1024x32
1. Chunk size of 1024x1024x256
    1. dir size: 2.1GB
    1. Time to build: 131m9.852s
    1. sections: 2000
    1. loading: stalled at 210/641 
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_1024x1024x256
1. Chunk size of 1024x1024x128
    1. dir size: 904MB
    1. Time to build: about an hour
    1. sections: 3500x2600x3000
    1. loading: ok, but stalled at 78/85
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_half_half
1. Chunk size of 256x256x128
    1. Time to build: 160m48.592s
    1. sections: 3943, 5184, 13312
    1. loading: ok 
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midsagittal
1. Chunk size of 256x256x128, mip=2
    1. Time to build: 159m55.436s
    1. sections: 7885x5184x13312
    1. loading: stalled at 118/276
    1. url: https://activebrainatlas.ucsd.edu/data/X/neuroglancer_data/mesh_midbrain
#### Images   
1. Chunk size of 256x256x32 image
    1. Time to build: 86m17.377s
    1. loading: painfully slow
    1. url: https://activebrainatlas.ucsd.edu/data/DK55/neuroglancer_data/C1
1. Chunk size of 128x128x64 image
    1. Time to build: 62m22.826s
    1. loading: much faster than above
    1. url: https://activebrainatlas.ucsd.edu/data/DK55/neuroglancer_data/C1
1. Chunk size of 256x256x128 image
    1. Time to build: 77m8.027s
    1. loading: kinda sluggish
    1. url: https://activebrainatlas.ucsd.edu/data/DK55/neuroglancer_data/C1
1. Chunk size of 64x64x64 image
    1. Time to build: 56m39.127s
    1. loading: ok, but lots of chunks to render
    1. url: https://activebrainatlas.ucsd.edu/data/DK55/neuroglancer_data/C1
1. Chunk size of 128x128x64 with 6 extra mips image
    1. Time to build: 54m34.380s
    1. loading: pretty good
    1. url: https://activebrainatlas.ucsd.edu/data/DK55/neuroglancer_data/C1
1. python create_neuroglancer_image.py --animal DK52 --channel 2 --downsample full
    1. Volume shape: (65000, 36000, 486)
    1. Working on 486 files with 8 cpus
    1. Create volume method took 12541.12985865702 seconds
    
### Notes
1. num_mips must be greater than 0, default is around 5 for full res, 3 for thumbnails.
1. using the hybrid neuroglancer-scripts and igneuos gives same slow result at 3x3x3
1. seung: chunk_size=[512, 512, 16] when volume size is [250000, 250000, 25000], res: [4,4,40]
1. at 1um, our volume size is 10368x7885x13312
1. sagittal slice 1um iostropic with 200 sections doesn't load all the way. chunk_size = [128,128,16]
1. dask still uses lots of RAM and dies at compute()
1. decrease chunk size when using a downsampled volume
1. Will recommendations: "The chunk size is pretty small. 64x64x64 results in relatively slow 
   loading times because the files are cut up so much. I'd recommend at least 128x128x64 
   or even 256x256x128."
1. Creating base chunk on DK39 on basalis with 3 cpus stalled.
1. Downsampling of DK39 at mips=1 took 1276m16.638s
