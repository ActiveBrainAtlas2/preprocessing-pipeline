# This folder contains the main files used to find the stack to stack transformations using simple itk as well as functions that deals with the simpleitk transformation objects.

## To find stact to stack transformation
`rough_alignment_affine.py` contains the main function to find image to image Affine transformation using simple itk.

`rough_alignment_demons.py` contains the main function to find image to image Demons transformation using simple itk.

### In general there are several steps to registeration including:
1. creating the `sitk.ImageRegistrationMethod()` method that handles the registration.
1. setting the optimization metric
1. setting the optimization method
1. setting the initial transformation
1. setting the options for multi-resolution based optimization
1. setting the report events that report the status of the optimization as it excutes
1. excuting the optimization

#### Functions are created for handling these steps. The generally takes the `ImageRegistrationMethod` object as input and have operations that changes some of its settings.
## To apply the transformation to points

`apply_affine_transform.py` Applies Affine transformation to a list of coms

`apply_demons_transform.py` Applies Demons transformation to a list of coms

These functions exists because applying the transformation obtained from stack to stack to alignment doesn't seem to be straight forward and there are not a lot of documentations available.  Whether they work as intended still needs to be tested.