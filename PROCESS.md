### Table of contents for the pipeline process
1. [Active Brain Atlas home page](https://github.com/ActiveBrainAtlas2)
1. [Installing the pipeline software](SETUP.md)
1. [A description of the pipeline process with detailed instructions](PROCESS.md)
1. [The entire MySQL database schema for the pipeline and the Django portal](schema.sql)
1. [Software design and organization](Design.md)

## Preprocessing using pipeline_utility
### Description
The pipeline process will take scanned images that are digitized into CZI files
and make them available in Neuroglancer. The process involves the following steps:
1. The user enters the [animal](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/slideczitotif/)
information into the database. The entire process depends on this initial step and will not
proceed without this initial information. Throughout the process, the database is checked
for information so it is vital for the correct information to be placed in these tables:
    1. [animal](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/slideczitotif/)
    1. [scan_run](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/scanrun/)
    1. [histology](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/histology/)

1. CZI files are placed on a network file system (NFS) which is named birdstore and is 
mounted at /net/birdstore on our 3 workstations:
    1. ratto
    1. basalis
    1. muralis
1. The location of the CZI files is: */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/czi*
1. CZI files are large compressed files containing around 20 images and a large amount of metadata that describes
the scanner and the scanned images. The images and metadata contained in each CZI file is extraced with a set of 
tools that are available on each workstation. The bioformat software is also available for download at: 
https://www.openmicroscopy.org/bio-formats/downloads/  
1. The metadata is yanked out of the CZI file with this command line tool: */usr/local/share/bftools/showinf*
1. The TIF images are yanked out with this tool: */usr/local/share/bftools/bfconvert*
1. The bioformat tools use Java so this must also be installed on the workstation.
1. The *bfconvert* tool pulls the TIF files out of the CZI files and puts them
in */net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX/tif*
1. The *showinf* tool takes the metadata and inserts/updates it into these tables in the database:
    1. [slide](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/slide/) 
    1. [slide_czi_to_tif](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/slideczitotif/)
    1. [scan_run](https://activebrainatlas.ucsd.edu/activebrainatlas/admin/brain/scanrun/)
### Setup
1. To install the software prerequisites, [look here.](README.md) Or use the installed virtual environment on ratto, basalis and muralis by running: 

```source /usr/local/share/pipeline/bin/activate```

1. To run any of these commands at high resolution, prefix each command with `nohup`and end the command with `&`. That will make it run in the background and you can log out.

1. All scripts that can be parallelized are done in the script with the get_cpus method.
   
## Preprocessing new scans starting with czi files.
1. Create a folder with brain id under /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DKXX create subfolder DKXX/czi and DKXX/tif.  Then copy the czi files to DKXX/czi.
   
1. Add entries in the animal, scan run and histology table in the database using the admin portal.  You can do this by using the corresponding app and clicking the button on the top right in the admin portal to create rows.
1. All functionality for running the pipeline is found in src/create_pipeline.py

   
1. Run: `python src/create_pipeline.py --animal DKXX`
    1. This will scan each czi file.
    1. Extracts the tif meta information and inserts into the slide_czi_to_tif.
    1. Also creates the tif files
    1. By default it works on channel 1 and the downsampled stack.
    1. After this is one you'll want to do the Django database portal QC on the slides
1. Have someone confirm the status of each slide in: https://activebrainatlas.ucsd.edu/activebrainatlas/admin
    1. After logging in, go to the Slides link in the Brain category.
    1. Enter the animal name in the search box.
    1. Under the PREP ID column, click the link of the slide you want to edit.
    1. If the entire slide is bad, mark it as Bad under Slide Status.
    1. If a scene needs to be marked as Bad, Out of Focus or the End slide, select the appropriate Scene QC.
    If you mark it as Bad or Out of Focus, the nearest neighbor will NOT be inserted. If you need to replicate
    a scene, you use replicate scene functionality in the appropriate scene in the form.
    1. If you want to replicate a scene, choose the Replicate field and add an amount to replicate.
    1. The list of scenes are listed near the bottom of the page.
    1. When you are done, click one of the Save buttons at the bottom of the page.
    1. After editing the slides, you can view the list of sections under the Sections link under Brain.
    
1. Run: `python src/create_pipeline.py --animal DKXX step 1`
    1. This will read the sections view in the database. 
    1. Creates the full and downsampled files
    1. Create the normalized files
    1. Create png files for channel 1.
    1. Creates the final masks
    1. You'll need to now verify the masks and possibly edit some of them in GIMP
    1. Check the rotation necessary for the images by viewing the normalized files and then 
    updating the scan run table in the Django database portal and update the rotations. It is usually 3.

1. Run: `python src/create_pipeline.py --animal DKXX --step 2`
    1. This will finalize the masks
    1. Creates the cleaned files from the masks
    1. Creates all the necessary histograms

1. Run: `python src/create_pipeline.py --animal DKXX --step 3`
    1. This will run elastix and create the rigid transformation for consecutive pair of files.
    1. Data is stored in the elastix_transformation table
    1. The alignment process is then run from the elastix data
    1. View the aligned images to make sure they all look good. ImageJ or geeqie 
    is good for viewing lots of files.
    
1. Run: `python src/create_pipeline.py --animal DKXX --step 4`
    1. This will create all the neuroglancer files in C1T_rechunkme and then C1T.
    C1T_rechunkme is the preliminary data directory that is created by the
    create_neuroglancer_image method and is then later used by the create_downsampling
    method.
    1. View results in neuroglancer. Add the layer to the precompute with:
        https://activebrainatlas.ucsd.edu/data/DKXX/neuroglancer_data/C1T
1. After you have completed the downampled version for channel 1, you can repeat
this entire process by running `python src/create_pipeline.py --animal DKXX --channel 2 --step 4`
This will run the entire process for channel 2. Most the steps will be automatically skipped.
1. Repeat the process again for channel 3. Once you are happy with all the results run
the process again but 
with `python src/create_pipeline.py --animal DKXX --channel 1 downsample false --step 4`
   ## Helper functions:
   1. To report number of files in each subdirectory:
   ```
   find . -type d -print0 | while read -d '' -r dir; do
       files=("$dir"/*)
       printf "%5d files in directory %s\n" "${#files[@]}" "$dir"
   done
   ```
