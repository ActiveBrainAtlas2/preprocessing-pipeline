
import h5py
import itk
import os

DATA = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/MD589/preps/CH1"
REGDATA = "/net/birdstore/Active_Atlas_Data/data_root/brains_info/registration"
hdfile = os.path.join(DATA, "registered/allen25um/init-transform.h5")
fixed_volume_path = os.path.join(REGDATA, "allen_100um_sagittal.tif")
moving_volume_path = os.path.join(DATA, "moving_volume.tif")

if not os.path.exists(hdfile):


    fixed_image = itk.imread(fixed_volume_path, itk.F)
    moving_image = itk.imread(moving_volume_path, itk.F)
    # init transform start
    # Translate to roughly position sample data on top of CCF data
    init_transform = itk.VersorRigid3DTransform[itk.D].New()  # Represents 3D rigid transformation with unit quaternion
    init_transform.SetIdentity()
    transform_initializer = itk.CenteredVersorTransformInitializer[
        type(fixed_image), type(moving_image)
    ].New()
    transform_initializer.SetFixedImage(fixed_image)
    transform_initializer.SetMovingImage(moving_image)
    transform_initializer.SetTransform(init_transform)
    transform_initializer.GeometryOn()  # We compute translation between the center of each image
    transform_initializer.ComputeRotationOff()  # We have previously verified that spatial orientation aligns
    transform_initializer.InitializeTransform()
    # initializer maps from the fixed image to the moving image,
    # whereas we want to map from the moving image to the fixed image.
    init_transform = init_transform.GetInverseTransform()
    print(init_transform)
    print()
    print(type(init_transform))
    print()
    init_transform

    itk.transformwrite([init_transform], hdfile)

print('Getting transform file')
init_transform = itk.transformread(hdfile)[0]
print(type(init_transform))
