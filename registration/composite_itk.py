#!/usr/bin/env python
import SimpleITK as sitk
import os, sys
import numpy as np


DIR = '/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK52'
INPUT = os.path.join(DIR, 'preps', 'CH1', 'thumbnail')
fixed_filename = os.path.join(INPUT, '200.tif')

angle = np.radians(33)
xshift = 130
yshift = 100


outputImageFile = "out.tif"
differenceImageAfterFile = "diffafter.tif"
differenceImageBeforeFile = "diffbefore.tif"

PixelType = sitk.sitkFloat32

fixed = sitk.ReadImage(fixed_filename, sitk.sitkFloat32)
transform = sitk.Euler2DTransform()
transform.SetCenter(np.array(fixed.GetSize()) / 2)
transform.SetAngle(angle)
transform.SetTranslation([xshift, yshift])
resample = sitk.ResampleImageFilter()
resample.SetReferenceImage(fixed)
resample.SetInterpolator(sitk.sitkLinear)
resample.SetDefaultPixelValue(0)
resample.SetOutputPixelType(fixed.GetPixelID())
resample.SetTransform(transform)
movingImage = resample.Execute(fixed)
