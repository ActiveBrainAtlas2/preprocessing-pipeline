from pathlib import Path
import SimpleITK as sitk
import toolbox.sitk
mov_brain = 'DK52'
fix_brain = 'DK43'
thumb_spacing = (10.4, 10.4, 20.0)
data_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data')
mov_img_thumb_dir = data_dir / mov_brain / 'preps/CH1/thumbnail_aligned'
fix_img_thumb_dir = data_dir / fix_brain / 'preps/CH1/thumbnail_aligned'
moving_image = toolbox.sitk.load_image_dir(mov_img_thumb_dir, spacing=thumb_spacing)
fixed_image = toolbox.sitk.load_image_dir(fix_img_thumb_dir, spacing=thumb_spacing)
moving_image = sitk.Cast(moving_image, sitk.sitkFloat32)
fixed_image = sitk.Cast(fixed_image, sitk.sitkFloat32)
centered_transform = sitk.CenteredTransformInitializer(
    fixed_image, moving_image,
    sitk.AffineTransform(3),
    sitk.CenteredTransformInitializerFilter.GEOMETRY
)
transform = centered_transform

registration_method = sitk.ImageRegistrationMethod()
registration_method.SetInterpolator(sitk.sitkLinear)

# Metric
registration_method.SetMetricAsDemons(10) #intensities are equal if the difference is less than 10HU

# Optimizer
# Running the Demons registration with the conjugate gradient optimizer takes a long time
# which is why the code below uses gradient descent.
# If you are more interested in accuracy and have the time
# then switch to the conjugate gradient optimizer.
#registration_method.SetOptimizerAsConjugateGradientLineSearch(...)
registration_method.SetOptimizerAsGradientDescent(
    learningRate=1.0,
    numberOfIterations=100,
    convergenceMinimumValue=1e-6,
    convergenceWindowSize=10
)
registration_method.SetOptimizerScalesFromPhysicalShift()

# Transformation
transform_to_displacment_field_filter = sitk.TransformToDisplacementFieldFilter()
transform_to_displacment_field_filter.SetReferenceImage(fixed_image)
demons_transform = sitk.DisplacementFieldTransform(transform_to_displacment_field_filter.Execute(affine_transform))
# Regularization (update field - viscous, total field - elastic)
demons_transform.SetSmoothingGaussianOnUpdate(
    varianceForUpdateField=0.0,
    varianceForTotalField=2.0
)
registration_method.SetInitialTransform(demons_transform)

# Multi-resolution
# We have a memory issue here. If we try to shrink with factor 2, memory will explode.
# registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
# registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[8, 4, 0])
registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4])
registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[8])
registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

# Plotting
registration_method.AddCommand(sitk.sitkStartEvent, start_plot)
registration_method.AddCommand(sitk.sitkEndEvent, end_plot)
registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent, update_multires_iterations)
registration_method.AddCommand(sitk.sitkIterationEvent, lambda: plot_values(registration_method))

registration_method.Execute(fixed_image, moving_image);