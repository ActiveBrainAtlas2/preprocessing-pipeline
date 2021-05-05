### New Brain
## Post CZI Creation Process
1. To install the software prerequisites, [look here.](README.md). Or just use the installed virtual environment on ratto, basalis and muralis: `source /usr/local/share/pipeline/bin/activate`
1. Running any of these commands at high resolution, you will want to prefix each command with `nohup`
   and put a '&' at the end of the command. That will make it run in the background and you can log out.
1. Run: `create_meta.py --animal DKXX`
    1. This will scan each czi file.
    2. Extracts the tif meta information and inserts into the slide_czi_to_tif.
    1. On basalis takes: 437m57.460s for 147 czi files.
    1. On muralis: 513m50.446s for 147 czi files.
    1. On ratto: 527m9.581s for 147 czi files.
1. Run: `python create_tifs.py --animal DKXX --channel 1` 
    1. This will read the sections view in the database. This can be run before the QC section
       below. Doing that will create some extra unused tifs, but that is not a problem.
    1. Create tif files for channel 1.
    1. Create png files for channel 1.
    1. Repeat process for the other 2 channels when ready.
1. Run `tif2jp2.sh DKXX` in programming/pipeline_utility/registration. This script runs Matlab so you must have a license.
1. Have someone confirm the status of each slide in: https://activebrainatlas.ucsd.edu/activebrainatlas/admin
    1. After logging in, go to the Slides link in the Brain category.
    1. Enter the animal name in the search box.
    1. Under the PREP ID column, click the link of the slide you want to edit.
    1. If the entire slide is bad, mark it as Bad under Slide Status.
    1. If a scene needs to be marked as Bad, Out of Focus or the End slide, select the appropriate Scene QC.
    If you mark it as Bad or Out of Focus, the nearest neighbor will be inserted.
    1. If you want to replicate a scene, choose the Replicate field and add an amount to replicate.
    1. The list of scenes are listed near the bottom of the page.
    1. When you are done, click one of the Save buttons at the bottom of the page.
    1. After editing the slides, you can view the list of sections under the Sections link under Brain.
1. Run: `python create_preps.py --animal DKXX --channel 1`
    1. This will fill the directory of the full and low resolution files for channel 1.
    1. Repeat process for the other 2 channels when ready.
    1. View a couple thumbnails to determine how much rotation/flips to perform.
1. Run: `python create_masks.py --animal DKXX`
    1. This will read the thumbnail directory and create masks in the DKXX/preps/thumbnail_masked dir.
    1. No need to use channel 2 or 3. It works solely on channel 1.
1. Run: `python create_histogram.py --animal DKXX --channel 1 --single single`
    1. This will read the directory of the thumbnail resolution files for channel 1.
    1. Create histogram for each files for channel 1.
    1. Repeat process for the other 2 channels when ready.
1. Run: `python create_clean.py --animal DKXX --channel 1`
    1. The necessary rotation and flip parameters must be in the scan run table..
    1. Be careful with the rotation and flip. To do a 90 degree right rotation requires rotation=1
    1. View a few of the files in DKXX/preps/CH1/thumbnail_cleaned.
    1. full resolution on ratto one channel takes 863 minutes. When it is finished, check file count
   and make sure there are no small files, especially with high resolution.
1. Run: `python create_elastix.py --animal DKXX`
    1. This will create the DKXX/preps/elastix directory and a subdirectory for each file pair.
    1. The elastix dir will be used to align the other channels and the full resoltions.
1. Run: `python create_alignment.py --animal DKXX --channel 1`
    1. This will use the DKXX/preps/elastix directory for the transformation parameters. It will then use PIL to do an affine transformation to do section to section alignment.
1. Run: `python create_web.py --animal DKXX`
    1. This will use the DKXX/preps/CH1/thumbnail_aligned directory for source images. It will then use PIL to do an create web viewable images.
1. Run: `python create_neuroglancer_image.py --animal DKXX --channel 1 --downsample true`
    1. This will create the data for neuroglancer for channel 1.
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C1T
1. When you are satisfied with the results, run these steps with full resolution on channel 1
    1. `python create_masks.py --animal DKXX --downsample false`
    1. `python create_clean.py --animal DKXX --channel 1 --downsample false`
    1. `python create_alignment.py --animal DKXX --channel 1 --downsample false`
    1. `python create_neuroglancer_image.py --animal DKXX --channel 1 --downsample false`
    1. `python create_downsampling.py --animal DKXX --channel 1 --downsample false`
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C1
1. When you are satisfied with the full resolution results, finish the other two channels
    1. `python create_clean.py --animal DKXX --channel 2 --downsample false`
    1. `python create_alignment.py --animal DKXX --channel 2 --downsample false`
    1. `python create_neuroglancer_image.py --animal DKXX --channel 2 --downsample false`
    1. `python create_downsampling.py --animal DKXX --channel 2 --downsample false`
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C2
    1. `python create_clean.py --animal DKXX --channel 3 --downsample false`
    1. `python create_alignment.py --animal DKXX --channel 3 --downsample false`
    1. `python create_neuroglancer_image.py --animal DKXX --channel 3 --downsample false`
    1. `python create_downsampling.py --animal DKXX --channel 3 --downsample false`
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C3
