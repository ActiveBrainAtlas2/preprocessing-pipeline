
import h5py
import itk
import os

DATA = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/MD589/preps/CH1"
REGDATA = "/net/birdstore/Active_Atlas_Data/data_root/brains_info/registration"
hdfile = os.path.join(DATA, "registered/allen25um/init-transform.hdf5")
fixed_volume_path = os.path.join(REGDATA, "allen_25um_sagittal.tif")
moving_volume_path = os.path.join(DATA, "moving_volume.tif")

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



with h5py.File(hdfile, "r") as f:
    # Print all root level object names (aka keys) 
    # these can be group or dataset names 
    print("Keys: %s" % f.keys())
    # get first object name/key; may or may NOT be a group
    a_group_key = list(f.keys())[0]

    # get the object type for a_group_key: usually group or dataset
    print(type(f[a_group_key])) 

    # If a_group_key is a group name, 
    # this gets the object names in the group and returns as a list
    data = list(f[a_group_key])
    print(data)
    # If a_group_key is a dataset name, 
    # this gets the dataset values and returns as a list
    #data = list(f[a_group_key])
    # preferred methods to get dataset values:
    #ds_obj = f[a_group_key]      # returns as a h5py dataset object
    #ds_arr = f[a_group_key][()]  # returns as a numpy array
    