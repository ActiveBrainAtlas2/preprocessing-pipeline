### Usability checklist

Here is a list of things to check after deploying software to the server

## Test Neurogolancer-Django interaction
1. login to https://activebrainatlas.ucsd.edu/activebrainatlas/admin
2. Check https://activebrainatlas.ucsd.edu/activebrainatlas/admin/neuroglancer/urlmodel/ and search for **test_save_annotation**. Open the neuroglancer link and create a copy of it by clicking new. 
3. create a new volume,add remove and move points and delete. 
4. create a com and cell and delete them. 
5. move the points around and click save annotation
6. open a new annotation layer and import the saved annotations from the drop down
7. locate the saved annotations in the admin portal.  Confirm that the coordinate match the data in neuroglancer and that the Animal ID, structure and annotator information is correct.
8. Delete the added test point after checking
9. Check https://activebrainatlas.ucsd.edu/activebrainatlas/admin/neuroglancer/urlmodel/ and search for **test save annotations**. Find the new entry you created and delete it using the action drop down. 

## Test Slide QC
1. open the slide option in the brain app
2. search for "test"
3. click into a test entry
4. disable scene one and click "save and continue"
5. enable scene one again and duplicate it, click "save and continue"
6. set scene one duplication to 0 again and click "save and continue"
check that the right QC result is applied for each step
