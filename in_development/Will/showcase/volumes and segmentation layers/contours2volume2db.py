from abakit.lib.Controllers.PolygonSequenceController import PolygonSequenceController
from abakit.lib.Controllers.TransformationController import TransformationController
from abakit.atlas.VolumeMaker import VolumeMaker
import pickle
polygon_controller = PolygonSequenceController()
volume = polygon_controller.get_volume(prep_id='DK55',annotator_id=1,structure_id=8)
transformation_controller = TransformationController()
transformation = transformation_controller.get_transformation(source='DK55',destination='Atlas',\
    transformation_type='Rigid')
transformed_points = transformation.forward_transform_points()
transformed_contours = ...
maker = VolumeMaker(animal='DK55')
maker.set_aligned_contours(transformed_contours)
maker.compute_COMs_origins_and_volumes()
mask_3d = maker.volumes['5N_L']
compression_function = lambda standin_for_compression: standin_for_compression
compressed_mask_3d = compression_function(mask_3d)
