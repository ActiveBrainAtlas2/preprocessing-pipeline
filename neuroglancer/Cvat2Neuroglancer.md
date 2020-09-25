#### Software Requirements for importing and exporting data from CVAT to Neuroglancer
1. Working with the original hand annotated structures
    1. Import original Yuncong hd5 files in pandas dataframes and CSV files
    1. Export clean non-dense vertices of the 28 main structures to CSV files for future use
    1. Import CSV data into CVAT with no simplifications.
    1. Retain the ability to modify these structures and then export this data into a
    Nueoroglancer volume. Have this volume available on 
    birdstore to a directory accessible by the webserver and neuroglancer precompute
    loading.
    
1. Make this process robust and seamless.
    1. The process of using the original annotations in CVAT should work consistently and easily.
    1. Users should be able to make modifications in CVAT and quickly see these same results in 
    Neuroglancer.
    1. Achieving this quick seamless method will involve the quick and error free method to:
        1. Export data from CVAT
        1. Create a numpy array holding the annotations from the export
        1. Create a precomputed volume
        1. Make volume available in the correct directory on birdstore
        1. Read volume as a precomputed layer in Neuroglancer
    1. End users should be able to perform the above method multiple times with ease.
