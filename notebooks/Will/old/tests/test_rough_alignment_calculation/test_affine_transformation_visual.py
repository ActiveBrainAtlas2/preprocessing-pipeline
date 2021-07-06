import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform
from notebooks.Will.toolbox.rough_alignment.sitk.utility import *
import matplotlib.pyplot as plt
#%%
prepi = 'DK39'
transform = get_affine_transform(prepi)
# %%
DK39,DK52 = get_fixed_and_moving_image('DK39','DK52')
# %%
centering_transform = sitk.CenteredTransformInitializer(
        DK39, DK52,
        sitk.AffineTransform(3),
        sitk.CenteredTransformInitializerFilter.GEOMETRY)
# %%
np39 = sitk.GetArrayFromImage(DK39)
np52 = sitk.GetArrayFromImage(DK52)

#%%
plt.imshow(np39[200]-np52[200])
#%%
sitk.Show(DK39, title="Visible Human Head")

# %%
def mask_image_multiply(mask, image):
    components_per_pixel = image.GetNumberOfComponentsPerPixel()
    if  components_per_pixel == 1:
        return mask*image
    else:
        return sitk.Compose([mask*sitk.VectorIndexSelectionCast(image,channel) for channel in range(components_per_pixel)])

def alpha_blend(image1, image2, alpha = 0.5, mask1=None,  mask2=None):
    '''
    Alaph blend two images, pixels can be scalars or vectors.
    The region that is alpha blended is controled by the given masks.
    '''
    
    if not mask1:
        mask1 = sitk.Image(image1.GetSize(), sitk.sitkFloat32) + 1.0
        mask1.CopyInformation(image1)
    else:
        mask1 = sitk.Cast(mask1, sitk.sitkFloat32)
    if not mask2:
        mask2 = sitk.Image(image2.GetSize(),sitk.sitkFloat32) + 1
        mask2.CopyInformation(image2)
    else:        
        mask2 = sitk.Cast(mask2, sitk.sitkFloat32)

    components_per_pixel = image1.GetNumberOfComponentsPerPixel()
    if components_per_pixel>1:
        img1 = sitk.Cast(image1, sitk.sitkVectorFloat32)
        img2 = sitk.Cast(image2, sitk.sitkVectorFloat32)
    else:
        img1 = sitk.Cast(image1, sitk.sitkFloat32)
        img2 = sitk.Cast(image2, sitk.sitkFloat32)
        
    intersection_mask = mask1*mask2
    
    intersection_image = mask_image_multiply(alpha*intersection_mask, img1) + \
                         mask_image_multiply((1-alpha)*intersection_mask, img2)
    return intersection_image + mask_image_multiply(mask2-intersection_mask, img2) + \
           mask_image_multiply(mask1-intersection_mask, img1)
#%%           