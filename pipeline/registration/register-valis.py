from valis import registration, feature_detectors, non_rigid_registrars, affine_optimizer
slide_src_dir = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK37/preps/CH1/thumbnail"
results_dst_dir = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK37/preps/CH1/results"
registered_slide_dst_dir = "/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK37/preps/CH1/registered"


# Select feature detector, affine optimizer, and non-rigid registration method.
# Will use KAZE for feature detection and description
# SimpleElastix will be used for non-rigid warping and affine optimization
feature_detector_cls = feature_detectors.KazeFD
non_rigid_registrar_cls = non_rigid_registrars.SimpleElastixWarper
affine_optimizer_cls = affine_optimizer.AffineOptimizerMattesMI

# Create a Valis object and use it to register the slides in slide_src_dir
registrar = registration.Valis(slide_src_dir, results_dst_dir,
                               feature_detector_cls=feature_detector_cls,
                               affine_optimizer_cls=affine_optimizer_cls,
                               non_rigid_registrar_cls=non_rigid_registrar_cls)

registrar.imgs_ordered=True

rigid_registrar, non_rigid_registrar, error_df = registrar.register()

registration.kill_jvm() # Kill the JVM