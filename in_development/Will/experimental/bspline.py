
from __future__ import print_function
import SimpleITK as sitk
import sys
import os
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.IOs.get_stack_image_sitk import load_stack_from_prepi

def command_iteration(method, bspline_transform) :
    if method.GetOptimizerIteration() == 0:
        # The BSpline is resized before the first optimizer
        # iteration is completed per level. Print the transform object
        # to show the adapted BSpline transform.
        print(bspline_transform)


    print("{0:3} = {1:10.5f}".format(method.GetOptimizerIteration(),
                                     method.GetMetricValue()))

def command_multi_iteration(method) :
    # The sitkMultiResolutionIterationEvent occurs before the
    # resolution of the transform. This event is used here to print
    # the status of the optimizer from the previous registration level.
    if R.GetCurrentLevel() > 0:
        print("Optimizer stop condition: {0}".format(R.GetOptimizerStopConditionDescription()))
        print(" Iteration: {0}".format(R.GetOptimizerIteration()))
        print(" Metric value: {0}".format(R.GetMetricValue()))

    print("--------- Resolution Changing ---------")


fixed = load_stack_from_prepi('DK39')
moving = load_stack_from_prepi('DK52')

transformDomainMeshSize=[2]*fixed.GetDimension()
tx = sitk.BSplineTransformInitializer(fixed,transformDomainMeshSize )

print("Initial Number of Parameters: {0}".format(tx.GetNumberOfParameters()))

R = sitk.ImageRegistrationMethod()
R.SetMetricAsJointHistogramMutualInformation()

R.SetOptimizerAsGradientDescentLineSearch(5.0,
                                          100,
                                          convergenceMinimumValue=1e-4,
                                          convergenceWindowSize=5)
R.SetInterpolator(sitk.sitkLinear)
R.SetInitialTransformAsBSpline(tx,inPlace=True,scaleFactors=[1,2,5])
R.SetShrinkFactorsPerLevel([4,2,1])
R.SetSmoothingSigmasPerLevel([4,2,1])
R.AddCommand( sitk.sitkIterationEvent, lambda: command_iteration(R, tx) )
R.AddCommand( sitk.sitkMultiResolutionIterationEvent, lambda: command_multi_iteration(R) )
outTx = R.Execute(fixed, moving)
print("-------")
print(tx)
print(outTx)
print("Optimizer stop condition: {0}".format(R.GetOptimizerStopConditionDescription()))
print(" Iteration: {0}".format(R.GetOptimizerIteration()))
print(" Metric value: {0}".format(R.GetMetricValue()))
sitk.WriteTransform(outTx,  'home/zhw272/data/bspline_dk52_dk39.tfm')

if ( not "SITK_NOSHOW" in os.environ ):

    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(fixed);
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(100)
    resampler.SetTransform(outTx)

    out = resampler.Execute(moving)
    simg1 = sitk.Cast(sitk.RescaleIntensity(fixed), sitk.sitkUInt8)
    simg2 = sitk.Cast(sitk.RescaleIntensity(out), sitk.sitkUInt8)
    cimg = sitk.Compose(simg1, simg2, simg1//2.+simg2//2.)
    sitk.Show( cimg, "Image Registration Composition" )
