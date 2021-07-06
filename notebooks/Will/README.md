# This directory contains code created by Zhongkai Wu (William) to accomplish the following:
* **Calculate** image to image Affine and Demons transfomation from DK52 to DKXX.
* **Load and apply** the transformation to images or com.
* **Visualize** differences between center of mass.

## Folder organization:
* **showcase**  contains examples and main scripts
* **toolbox** contains libries used in the examples
* **old** contains depricated files
* **experimental**  contains functions that are not fully polished

## running the functions from notebook or script
if the folder is not on the default search path of python you can mannually add it by including this code in the start of your notebook or script.
```python
import sys
sys.path.append('/path_to_github_folder/pipeline_utility')
```

## Calculate image to image Affine and Demons transfomation from DK52 to DKXX.
* To find the image to image affine transformation:
``` python
from notebooks.Will.toolbox.rough_alignment.rough_alignment_affine import get_rough_alignment_affine_transform
transformi = get_rough_alignment_affine_transform(moving_brain ='DK52',fixed_brain = 'DKXX')
```
* To find the image to image demons transformation:
``` python
from notebooks.Will.toolbox.rough_alignment.rough_alignment_demons import get_rough_alignment_demons_transform
transformi = get_rough_alignment_demons_transform(moving_brain ='DK52',fixed_brain = 'DKXX')
```
Examples for finding the image to image Affine and Demons transformation can be found in the showcase
## Load and apply the transformation to images or com.
The image to image transformations are stored at: 

```
/net/birdstore/Active_Atlas_Data/data_root/tfm/affine/DKXX_affine.tfm
```
and
```
/net/birdstore/Active_Atlas_Data/data_root/tfm/demons/DKXX_demons.tfm
```
* To load the computed Affine transformation:
``` python
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
affine_transform = get_affine_transform('DKXX')
```
* To load the computed Demons transformation:
``` python
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_demons_transform
demons_transform = get_demons_transform('DKXX')
```
These utility function handles the save path and loading the transformation files
* To apply the computed transformation to an image stack:
```python
import Simpleitk as sitk
from notebooks.Will.toolbox.IOs.get_stack_image_sitk import load_stack_from_prepi
moving_image = load_stack_from_prepi('DK52')
fixed_image = load_stack_from_prepi('DKXX')
transformed_image = sitk.Resample(
    moving_image, fixed_image, transform,
    sitk.sitkLinear, 0.0, moving_image.GetPixelID())
```
* To apply the computed Affine transformation to a list or array of coms:
```python
from notebooks.Will.toolbox.rough_alignment.apply_affine_transform import transform_point_affine
transformed_com = transform_point_affine(com_list)
```
* To apply the computed Demons transformation to a list or array of coms:
```python
from notebooks.Will.toolbox.rough_alignment.apply_demons_transform import transform_point_demons
transformed_com = transform_point_demons(com_list)
```
These two functions calls
```
transform.TransformPoint(com)
```
where `transform` is any transform object in Simple itk.  Whether these behave as expected is **still being tested**.
## Visualize differences between center of mass.
functions to create box plots for difference between coms in the x,y,z direction and the overall distance can be found in 
`
toolbox\plotting\plot_com_offset.py
`

To plot offset between two set of coms:
```python
from notebooks.Will.toolbox.plotting.plot_com_offset import *
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_all_landmarks_in_specimens

def get_prep_list_for_rough_alignment_test():
    return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55']
    
prep_list_function = get_prep_list_for_rough_alignment_test
landmark_list_function = get_all_landmarks_in_specimens
```
* *preps* or preparations refer to the brain specimens eg: DKXX
* *prep_list_function* is a function that returns a list of preps to examine.  This could be a function that queries the database or simply returns a list of strings.
* *landmark_list_function* is a function to determine the list of structures to include. 
eg:get_all_landmarks_in_specimens finds the union of all structures in each prep.  This deals with the case when the comparing brains with differented annotated list of landmark structures.

```python
plot_offset_between_two_com_sets(com_list_1,com_list_2,prep_list_function,landmark_list_function,plot_title)
```
* *plot_offset_between_two_com_sets* plots the boxplot of difference between two sets of center of mass in a pairwise manner.  com_list_1 and com_list_2 are list of com dictionaries and elements of the two lists are compared in a pairwise manner. 
```python
plot_offset_from_coms_to_a_reference(com_list,reference,prep_list_function,landmark_list_function,plot_title)
```
*plot_offset_from_coms_to_a_reference* plots the boxplot of difference between one set of center of mass to a single com dictionary called the reference.  The reference could be the atlas coms or a reference brain.  com_list is a list of com dictionaries and eacg element of the list is compared to the reference com. 
### to return matplotlib figures for producing a high resolution pdf document:

```python
figure = get_fig_offset_between_two_com_sets(com_list_1,com_list_2,prep_list_function,landmark_list_function,plot_title)
```
or
```python
figure = get_fig_offset_from_coms_to_a_reference(com_list,reference,prep_list_function,landmark_list_function,plot_title)
```
and then:
```python
from matplotlib.backends.backend_pdf import PdfPages
with PdfPages('../../...pdf') as pdf:
    pdf.savefig(figure)
```

## Experimental functions:
The experimental folder contains code to visualize the result of Affine and demons transformation in neuroglancer, as well as code to compare the different transformation.
