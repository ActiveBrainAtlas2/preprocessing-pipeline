import os
from lib.Controllers.SqlController import SqlController
from lib.Transformation import Transformation
import SimpleITK as sitk
import pickle
controller = SqlController('Atlas')
storage_folder = '/net/birdstore/Active_Atlas_Data/data_root/tfm/affine'
files = os.listdir(storage_folder)
for filei in files:
    affine_transform = sitk.ReadTransform(storage_folder + '/' + filei)
    transform = sitk.AffineTransform(3)
    transform.SetParameters(affine_transform.GetParameters())
    transform.SetFixedParameters(affine_transform.GetFixedParameters())
    # print(transform)
    transform = Transformation(transform)
    transform = pickle.dumps(transform)
    braini = filei.split('_')[0]
    controller.add_transformation_row(source = braini,destination = 'DK52',transformation_type = 5,transformation = transform)


print(files)