import numpy as np
from skimage import io
import os
import SimpleITK as sitk
from os.path import expanduser
HOME = expanduser("~")

#DIR = os.path.join(HOME, 'programming', 'dk39')
DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK39'
INPUT = os.path.join(DIR, 'tif')
ORIENTED = os.path.join(DIR, 'preps', 'oriented')
ALIGNED = os.path.join(DIR, 'preps', 'aligned')
PREALIGNED = os.path.join(DIR, 'preps', 'prealigned')
INPUTS = sorted(os.listdir(INPUT))
BADS = ['DK39_ID_0001_slide001_S1_C1.tif', 'DK39_ID_0004_slide001_S4_C1.tif', 
        'DK39_ID_0007_slide001_S2_C1.tif', 'DK39_ID_0010_slide001_S3_C1.tif', 'DK39_ID_0013_slide002_S1_C1.tif']
INPUTS = sorted([i for i in INPUTS if i not in BADS and '_C1' in i])


def everything(img, rotation):
    img = get_last_2d(img)
    img = np.rot90(img, rotation)
    return img.astype('uint16')

def get_last_2d(data):
    if data.ndim <= 2:
        return data    
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)


# orient images
for i in (INPUTS):
    infile = os.path.join(INPUT, i)
    outfile = os.path.join(ORIENTED, i)
    if os.path.exists(outfile):
        continue
    img = io.imread(infile)
    img = everything(img, 3)
    print('Saving oriented image')
    io.imsave(outfile, img, check_contrast=False)
    img = None


ORIENTS = sorted(os.listdir(ORIENTED))

fixedFilename = os.path.join(ORIENTED, ORIENTS[0])
movingFilename = os.path.join(ORIENTED, ORIENTS[1])
fixedImage = sitk.ReadImage(fixedFilename)
movingImage = sitk.ReadImage(movingFilename)
print('Loaded fixed and moving')
parameterMap = sitk.GetDefaultParameterMap('translation')
#parameterMap = sitk.GetDefaultParameterMap("rigid")
#parameterMap["Transform"] = ["AffineTransform"]
print('Post parameter map')
elastixImageFilter = sitk.ElastixImageFilter()
elastixImageFilter.SetFixedImage(fixedImage)
elastixImageFilter.SetMovingImage(movingImage)
elastixImageFilter.SetParameterMap(parameterMap)
elastixImageFilter.Execute()
print('Post execute')
resultImage = elastixImageFilter.GetResultImage()
transformParameterMap = elastixImageFilter.GetTransformParameterMap()

transformixImageFilter = sitk.TransformixImageFilter()
transformixImageFilter.SetTransformParameterMap(transformParameterMap)
print(ORIENTS)    
for filename in ORIENTS:
    input_file = os.path.join(ORIENTED, filename)
    transformixImageFilter.SetMovingImage(sitk.ReadImage(input_file))
    transformixImageFilter.Execute()
    filepath = os.path.join(PREALIGNED,filename)
    print("Creating :",filepath)
    sitk.WriteImage(transformixImageFilter.GetResultImage(), filepath)

"""
INPUT = PREALIGNED
OUTPUT = ALIGNED
INPUTS = sorted(os.listdir(INPUT))

for i in INPUTS:
    
    infile = os.path.join(INPUT, i)
    img = io.imread(infile)
    
    outfile = os.path.join(OUTPUT, i)
    #print('saving file', outfile)
    io.imsave(outfile, img.astype('uint16'), check_contrast=False)
    img = None
"""
