import sys
import numpy as np
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.IOs.get_calculated_transforms import get_affine_transform,get_demons_transform
import SimpleITK as sitk
affine_path43 = '/home/zhw272/programming/pipeline_utility/notebooks/Bili/data/automatic-alignment/DK43/1-affine.tfm'
transform = sitk.ReadTransform(affine_path43)
affine_path43_will = get_affine_transform('DK43')
print(transform)
print(affine_path43_will)