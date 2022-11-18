File manipulation modules
-------------------------

These files contain classes and methods used in peforming actual maninpulations
on the numpy arrays (the images). This involves:

- CZI extraction
- Metadata extraction
- Histogram creation
- Mask creation
- Image cleaning
- Image alignment
- Neuroglancer precomputed data creation
- Parallel process management of image manipulation


.. toctree::
   :titlesonly:
   :maxdepth: 2
   :caption: Image manipulation
   :hidden:

   image_manipulation/czi_manager.rst
   image_manipulation/elastix_manager.rst
   image_manipulation/filelocation_manager.rst
   image_manipulation/histogram_maker.rst
   image_manipulation/image_cleaner.rst
   image_manipulation/mask_manager.rst
   image_manipulation/meta_manager.rst
   image_manipulation/neuroglancer_manager.rst
   image_manipulation/normalizer_manager.rst
   image_manipulation/pipeline_process.rst
   image_manipulation/parallel_manager.rst
   image_manipulation/precomputed_manager.rst
   image_manipulation/prep_manager.rst
   image_manipulation/progress_manager.rst
   image_manipulation/tiff_extractor_manager.rst
   