import SimpleITK as sitk
class SiktAffineTransform:
    def __init__(self):
        self.save_path = '/net/birdstore/Active_Atlas_Data/data_root/tfm'
    
    def get_prepi_affine_transform(self,prepi):
        transform = sitk.ReadTransform(self.save_path + '/affine/' + prepi + '_affine.tfm')
        return transform
    
    def get_transform_images(image,moving_image,fixed_image,transform):
        sitk.Resample(moving_image, fixed_image, transform,sitk.sitkLinear, 0.0, moving_image.GetPixelID())