### New Brain
## Post CZI Creation Process
1. To install the software prerequisites, [look here.](README.md)
1. Run: create_meta.py --animal DKXX
    1. This will scan each czi file
    2. extract the tif meta information and insert into the slide_czi_to_tif table
1. Have someone confirm the status of each slide in: https://activebrainatlas.ucsd.edu/activebrainatlas/admin
    1. After logging in, go to the Slides link in the Brain category
    1. Enter the animal name in the search box
    1. Under the PREP ID column, click the link of the slide you want to edit
    1. If the entire slide is bad, make it as bad under Slide Status
    1. If Scene needs to be marked as Bad, Out of focus or the end slide, select the appropriate Scene QC. 
    If you mark it as Bad or out of focus, the nearest neighbor will be inserted.
    1. If you want to replicate a scene, choose the Replicate field and add an amount to replicate.
    1. The list of scenes are listed near the bottom of the page. 
    1. When you are done, click one of the Save buttons at the bottom of the page
    1. After editing the slides, you can view the list of sections under the Sections link under Brain
1. Run: python create_tifs.py --animal DKXX --channel 1 
    1. this will read the sections table in the database
    1. create tif files for channel 1
    1. repeat process for the other 2 channels when ready
1. Run: python create_thumbnails.py --animal DKXX --channel 1 
    1. this will read the directory of the full resolution files for channel 1
    1. create thumbnail tif files for channel 1
    1. repeat process for the other 2 channels when ready
    1. View a couple thumbnails to determine how much rotation/flips to perform
1. Run: python create_masks.py --animal DKXX
    1. This will read the thumbnail directory and create masks in the DKXX/preps/thumbnail_masked dir
    1. No need to use channel 2 or 3. It works solely on channel 1
1. Run: python create_clean.py --animal DKXX --channel 1 --rotation 1
    1. use the necessary rotations and flip/flop parameters
    1. view a few of the files in DKXX/preps/CH1/thumbnail_cleaned
1. Run: python create_alignment.py --animal DKXX --channel 1
    1. This will create the DKXX/preps/elastix directory and a subdirectory for each file pair
    1. The elastix dir will be used to align the other channels and the full resoltions
1. Run: python create_neuroglancer.py --animal DKXX --channel 1 --resolution thumbnail
    1. This will create the data for neuroglancer for channel 1
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C1T
1. When you are satisfied with the results, run these steps with full resolution on channel 1
    1. python create_masks.py --animal DKXX --resolution full
    1. python create_masks.py --animal DKXX --channel 1 --rotation 1 --resolution full
    1. python create_alignment.py --animal DKXX --channel 1 --resolution full
    1. python create_neuroglancer.py --animal DKXX --channel 1 --resolution full
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C1
1. When you are satisfied with the full resolution results, finishe the other two channels
    1. python create_clean.py --animal DKXX --channel 2 --rotation 1 --resolution full
    1. python create_alignment.py --animal DKXX --channel 2 --resolution full
    1. python create_neuroglancer.py --animal DKXX --channel 2 --resolution full
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C2
    1. python create_clean.py --animal DKXX --channel 3 --rotation 1 --resolution full
    1. python create_alignment.py --animal DKXX --channel 3 --resolution full
    1. python create_neuroglancer.py --animal DKXX --channel 3 --resolution full
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C3
