## Terminology:
3D mask:  A 3d numpy boolean/unsigned int8 array made from contours


modules:  python files that are imported


scripts:   python files that are executed from the command

## Coding Standards:
1. Functions should be implemented in classes that are modular and have clear boundaries between them.  Each class should perform a simple clearly defined role.
2. Each function method and class should have a descriptive docstring.
3. Each class should be tested

## Storing the polygon data and the 3d Volumes:
After the anatomist has entered the polygon data, the following step happens:
1. Fetching the polygon data from the database,
 - code: [PolygonSequenceController](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/lib/Controllers/PolygonSequenceController.py) , testing: pending
2. Transforming polygon data to atlas space
 - code: [brain_to_atlas_transform](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/registration/algorithm.py), testing: pending
3. Creating the 3D mask and origins from polygon data
 - code: [VolumeMaker](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/VolumeMaker.py), testing: [test_volume_maker](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/tests/test_volume_maker.py)
4. Compressing the 3D mask with encoding methods
 - code: pending, testing: pending
5. Storing the 3D mask and origins in the DB as pickled data. 
 - code: currently exist in scripts and will be organized, testing: pending

### Clarification needed:
Are we implementing this for the split table?
## Converting the 3d Volumes into neuroglancer meshes:
This step is performed with the Seung Lab Cloudvolume software

The Cloudvolume software Takes:
 - A 3d mask of integers 
 - A dictionary that contains the color and text related to each integer
 - Units and origins

 and creates:
    
- the segmentation layer viewable in neuroglancer

### Case1:  Converting a single structure to segmentation layer:
 - Code: [NgConverter](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/NgSegmentMaker.py) testing: [test_ng_segment_maker.py](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/tests/test_ng_segment_maker.py)
### Case2:  Converting all the structures in one brain to segmentation layer:
This involves 2 steps:
1. Assembling the origins and 3d masks for each structure into one big mask
 - Code: [Assembler](https://github.com/ActiveBrainAtlas2/abakit/blob/dev/src/abakit/atlas/Assembler.py) testing: pending
2. Converting the big mask to neuroglancer segmentation layer
 - code and testing: same as case1

    **note: This step is not doable in full resolution right now even on muralis.  It requires the creation of a matrix that is too big to store in memory.**

    To show brain structures in full resolution we need to change the way segmentation layer functions in neuroglancer to allow origins to be passed in per structure, and do not assign int8 values to spaces that are filled with 0.

### Clarification needed:
Are we storing and computing full resolution or downsampled masks?
Are we implementing the code to show one structure or multiple?

### Yoav's Questions:
What is the dtype of the 3D-mesh? should be unsigned int 8.
 - I believe that is the case 

What is stored in the database? a pickled 3D mask? That can be pretty large for large structures.
 - We designed the database to store pickled 3d masks.  We are waiting for your compression algorism before storing any full resolution masks

Can you define the interface between the code and Cloudvolume? 
Is it done through calls to a functions or class methods? What are the parameters? Or is CloudVolume executed as a separate unix process?
- cloud volume is a package written in python.  Here are the method calls to create a segmentation layer:

```python

info = CloudVolume.create_new_info(
    num_channels    = 1,
    layer_type      = 'segmentation',
    data_type       = 'uint8', # Channel images might be 'uint8'
    # raw, png, jpeg, compressed_segmentation, fpzip, kempressed, compresso
    encoding        = 'raw', 
    resolution      = [4, 4, 40], # Voxel scaling, units are in nanometers
    voxel_offset    = [0, 0, 0], # x,y,z offset in voxels from the origin
    mesh            = 'mesh',
    # Pick a convenient size for your underlying chunk representation
    # Powers of two are recommended, doesn't need to cover image exactly
    chunk_size      = [ 512, 512, 16 ], # units are voxels
    volume_size     = [ 250000, 250000, 25000 ], # e.g. a cubic millimeter dataset
)
vol = CloudVolume(cfg.path, info=info)
vol.commit_info()
vol[:, :, :] = 3d_mask
```

running commit_info creates a file named info in the output directory.  The segment propperities are then provided by editing the info file. 
