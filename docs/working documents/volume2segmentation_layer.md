## Converting the 3d Volumes into neuroglancer meshes:
This step is performed with the Seung Lab Cloudvolume software

The Cloudvolume software Takes:
 - A 3d mask of integers 
 - A dictionary that contains the color and text related to each integer
 - Units and origins

 and creates:
    
- the segmentation layer viewable in neuroglancer

### Case1:  Converting a single structure to segmentation layer:
 1. Getting the 3d mask from the database
  - code: currently exist in scripts and will be organized, testing: pending

 2. converting the 3d mask to the neuroglancer segmentation layer

   The [NgConverter](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/atlas/NgSegmentMaker.py) class converts the 3d mask to the segmentation layer.  The segmentation layer consists of a set of folders living on the file system. inhereits from the [NumpyToNeuroglancer](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/lib/utilities_cvat_neuroglancer.py).  The [NumpyToNeuroglancer](https://github.com/ActiveBrainAtlas2/abakit/blob/master/src/abakit/lib/utilities_cvat_neuroglancer.py) was produced by Yungcong and is able to produce eith Image layers or Segmentation layers from numpy arrays.

   The NumpyToNeuroglancer class uses the function `init_precomputed` to initiate the creation of a neuroglancer layer using the Seung lab CloudVolume package.  The specific calls to the package looks like:
   ```
   info = CloudVolume.create_new_info(
            num_channels=self.num_channels,
            layer_type=self.layer_type,  # 'image' or 'segmentation'
            data_type=self.data_type,  #
            encoding='raw',  # other options: 'jpeg', 'compressed_segmentation' (req. uint32 or uint64)
            resolution=self.scales,  # Size of X,Y,Z pixels in nanometers,
            voxel_offset=self.offset,  # values X,Y,Z values in voxels
            chunk_size=self.chunk_size,  # rechunk of image X,Y,Z in voxels
            volume_size=volume_size,  # X,Y,Z size in voxels
        )
    self.precomputed_vol = CloudVolume(f'file://{path}', mip=0, info=info, compress=True, progress=False)
    self.precomputed_vol.commit_info()
    self.precomputed_vol.commit_provenance()
   ```
   Where the `path` variable is the output path.  Then the information of each segment(in this case brain regions), including the color value and text descriptions are set using the `add_segment_properties` function.

   The volume is passed to NgConverter by 

   ```self.precomputed_vol[:, :, :] = self.volume```

   And the segmentation layer is created by 
   ```
   self.add_downsampled_volumes()
    self.add_segmentation_mesh()
   ```