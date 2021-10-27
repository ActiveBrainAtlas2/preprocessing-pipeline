import SimpleITK as sitk

def get_demons_transform(braini):
    save_path = '/net/birdstore/Active_Atlas_Data/data_root/tfm'
    transform = sitk.ReadTransform(save_path + '/demons/' + braini + '_demons.tfm')
    return transform

def get_affine_transform(braini):
    save_path = '/net/birdstore/Active_Atlas_Data/data_root/tfm'
    transform = sitk.ReadTransform(save_path + '/affine/' + braini + '_affine.tfm')
    return transform