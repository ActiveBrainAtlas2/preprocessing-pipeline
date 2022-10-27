import os
import sys
import SimpleITK as sitk



def lines_that_start_with(string, fp):
    return [line for line in fp if line.startswith(string)]

def getMetricValue(logpath):
    with open(logpath, "r") as fp:
        for line in lines_that_start_with("Final", fp):
            return line

def align_elastix(fixed_file, moving_file, moving_index):
    pixelType = sitk.sitkFloat32
    fixed = sitk.ReadImage(fixed_file, pixelType)
    moving = sitk.ReadImage(moving_file, pixelType)

    elastixImageFilter = sitk.ElastixImageFilter()
    elastixImageFilter.SetFixedImage(fixed)
    elastixImageFilter.SetMovingImage(moving)
    rigid_params = elastixImageFilter.GetDefaultParameterMap("rigid")

    rigid_params["AutomaticTransformInitializationMethod"] = [
        "GeometricalCenter"
    ]
    rigid_params["ShowExactMetricValue"] = ["false"]
    rigid_params["CheckNumberOfSamples"] = ["true"]
    rigid_params["NumberOfSpatialSamples"] = ["5000"]
    rigid_params["SubtractMean"] = ["true"]
    rigid_params["MaximumNumberOfSamplingAttempts"] = ["0"]
    rigid_params["SigmoidInitialTime"] = ["0"]
    rigid_params["MaxBandCovSize"] = ["192"]
    rigid_params["NumberOfBandStructureSamples"] = ["10"]
    rigid_params["UseAdaptiveStepSizes"] = ["true"]
    rigid_params["AutomaticParameterEstimation"] = ["true"]
    rigid_params["MaximumStepLength"] = ["10"]
    rigid_params["NumberOfGradientMeasurements"] = ["0"]
    rigid_params["NumberOfJacobianMeasurements"] = ["1000"]
    rigid_params["NumberOfSamplesForExactGradient"] = ["100000"]
    rigid_params["SigmoidScaleFactor"] = ["0.1"]
    rigid_params["ASGDParameterEstimationMethod"] = ["Original"]
    rigid_params["UseMultiThreadingForMetrics"] = ["true"]
    rigid_params["SP_A"] = ["20"]
    rigid_params["UseConstantStep"] = ["false"]
    ## The internal pixel type, used for internal computations
    ## Leave to float in general.
    ## NB: this is not the type of the input images! The pixel
    ## type of the input images is automatically read from the
    ## images themselves.
    ## This setting can be changed to "short" to save some memory
    ## in case of very large 3D images.
    rigid_params["FixedInternalImagePixelType"] = ["float"]
    rigid_params["MovingInternalImagePixelType"] = ["float"]
    ## note that some other settings may have to specified
    ## for each dimension separately.
    rigid_params["FixedImageDimension"] = ["2"]
    rigid_params["MovingImageDimension"] = ["2"]
    ## Specify whether you want to take into account the so-called
    ## direction cosines of the images. Recommended: true.
    ## In some cases, the direction cosines of the image are corrupt,
    ## due to image format conversions for example. In that case, you
    ## may want to set this option to "false".
    rigid_params["UseDirectionCosines"] = ["true"]
    ## **************** Main Components **************************
    ## The following components should usually be left as they are:
    rigid_params["Registration"] = ["MultiResolutionRegistration"]
    rigid_params["Interpolator"] = ["BSplineInterpolator"]
    rigid_params["ResampleInterpolator"] = ["FinalBSplineInterpolator"]
    rigid_params["Resampler"] = ["DefaultResampler"]
    ## These may be changed to Fixed/MovingSmoothingImagePyramid.
    ## See the manual.
    ##(FixedImagePyramid "FixedRecursiveImagePyramid']
    ##(MovingImagePyramid "MovingRecursiveImagePyramid']
    rigid_params["FixedImagePyramid"] = ["FixedSmoothingImagePyramid"]
    rigid_params["MovingImagePyramid"] = [
        "MovingSmoothingImagePyramid"
    ]
    ## The following components are most important:
    ## The optimizer AdaptiveStochasticGradientDescent (ASGD) works
    ## quite ok in general. The Transform and Metric are important
    ## and need to be chosen careful for each application. See manual.
    rigid_params["Optimizer"] = ["AdaptiveStochasticGradientDescent"]
    rigid_params["Transform"] = ["EulerTransform"]
    ##(Metric "AdvancedMattesMutualInformation")
    ## testing 17 dec
    rigid_params["Metric"] = ["AdvancedNormalizedCorrelation"]
    ## ***************** Transformation **************************
    ## Scales the rotations compared to the translations, to make
    ## sure they are in the same range. In general, it's best to
    ## use automatic scales estimation:
    rigid_params["AutomaticScalesEstimation"] = ["true"]
    ## Automatically guess an initial translation by aligning the
    ## geometric centers of the fixed and moving.
    rigid_params["AutomaticTransformInitialization"] = ["true"]
    ## Whether transforms are combined by composition or by addition.
    ## In generally, Compose is the best option in most cases.
    ## It does not influence the results very much.
    rigid_params["HowToCombineTransforms"] = ["Compose"]
    ## ******************* Similarity measure *********************
    ## Number of grey level bins in each resolution level,
    ## for the mutual information. 16 or 32 usually works fine.
    ## You could also employ a hierarchical strategy:
    ##(NumberOfHistogramBins 16 32 64)
    rigid_params["NumberOfHistogramBins"] = ["32"]
    ## If you use a mask, this option is important.
    ## If the mask serves as region of interest, set it to false.
    ## If the mask indicates which pixels are valid, then set it to true.
    ## If you do not use a mask, the option doesn't matter.
    rigid_params["ErodeMask"] = ["false"]
    ## ******************** Multiresolution **********************
    ## The number of resolutions. 1 Is only enough if the expected
    ## deformations are small. 3 or 4 mostly works fine. For large
    ## images and large deformations, 5 or 6 may even be useful.
    rigid_params["NumberOfResolutions"] = ["6"]
    ##(FinalGridSpacingInVoxels 8.0 8.0)
    ##(GridSpacingSchedule 6.0 6.0 4.0 4.0 2.5 2.5 1.0 1.0)
    ## The downsampling/blurring factors for the image pyramids.
    ## By default, the images are downsampled by a factor of 2
    ## compared to the next resolution.
    ## So, in 2D, with 4 resolutions, the following schedule is used:
    ##(ImagePyramidSchedule 4 4  2 2  1 1 )
    ## And in 3D:
    ##(ImagePyramidSchedule 8 8 8  4 4 4  2 2 2  1 1 1 )
    ## You can specify any schedule, for example:
    ##(ImagePyramidSchedule 4 4  4 3  2 1  1 1 )
    ## Make sure that the number of elements equals the number
    ## of resolutions times the image dimension.
    ## ******************* Optimizer ****************************
    ## Maximum number of iterations in each resolution level:
    ## 200-500 works usually fine for rigid registration.
    ## For more robustness, you may increase this to 1000-2000.
    ## 80 good results, 7 minutes on basalis with 4 jobs
    ## 200 good results except for 1st couple were not aligned, 12 minutes
    ## 500 is best, including first sections, basalis took 21 minutes
    num_iterations = "1000"
    rigid_params["MaximumNumberOfIterations"] = [num_iterations]
    ## The step size of the optimizer, in mm. By default the voxel size is used.
    ## which usually works well. In case of unusual high-resolution images
    ## (eg histology) it is necessary to increase this value a bit, to the size
    ## of the "smallest visible structure" in the image:
    ##(MaximumStepLength 4)
    ## **************** Image sampling **********************
    ## Number of spatial samples used to compute the mutual
    ## information (and its derivative) in each iteration.
    ## With an AdaptiveStochasticGradientDescent optimizer,
    ## in combination with the two options below, around 2000
    ## samples may already suffice.
    ##(NumberOfSpatialSamples 2048)
    ## Refresh these spatial samples in every iteration, and select
    ## them randomly. See the manual for information on other sampling
    ## strategies.
    rigid_params["NewSamplesEveryIteration"] = ["true"]
    rigid_params["ImageSampler"] = ["Random"]
    ## ************* Interpolation and Resampling ****************
    ## Order of B-Spline interpolation used during registration/optimisation.
    ## It may improve accuracy if you set this to 3. Never use 0.
    ## An order of 1 gives linear interpolation. This is in most
    ## applications a good choice.
    rigid_params["BSplineInterpolationOrder"] = ["1"]
    ## Order of B-Spline interpolation used for applying the final
    ## deformation.
    ## 3 gives good accuracy; recommended in most cases.
    ## 1 gives worse accuracy (linear interpolation)
    ## 0 gives worst accuracy, but is appropriate for binary images
    ## (masks, segmentations); equivalent to nearest neighbor interpolation.
    rigid_params["FinalBSplineInterpolationOrder"] = ["3"]
    ##Default pixel value for pixels that come from outside the picture:
    rigid_params["DefaultPixelValue"] = ["0"]
    ## Choose whether to generate the deformed moving image.
    ## You can save some time by setting this to false, if you are
    ## only interested in the final (nonrigidly) deformed moving image
    ## for example.
    rigid_params["WriteResultImage"] = ["false"]
    ## The pixel type and format of the resulting deformed moving image
    rigid_params["ResultImagePixelType"] = ["unsigned char"]
    rigid_params["ResultImageFormat"] = ["tif"]
    rigid_params["RequiredRatioOfValidSamples"] = ["0.05"]
    elastixImageFilter.SetParameterMap(rigid_params)
    elastixImageFilter.LogToConsoleOff()
    elastixImageFilter.LogToConsoleOff();
    elastixImageFilter.LogToFileOn();
    logfile = str(moving_index).zfill(3) + ".tif"
    elastixImageFilter.SetOutputDirectory('/tmp/elastix');
    elastixImageFilter.SetLogFileName(logfile);    
    elastixImageFilter.Execute()
    logpath = os.path.join('/tmp/elastix', logfile)
    metric_value = getMetricValue(logpath)
    print(metric_value)




if __name__ == '__main__':
    fixed = sys.argv[1]
    moving = sys.argv[2]
    moving_index = os.path.basename(moving)
    moving_index = str(moving_index).replace(".tif","")
    align_elastix(fixed, moving, moving_index)

