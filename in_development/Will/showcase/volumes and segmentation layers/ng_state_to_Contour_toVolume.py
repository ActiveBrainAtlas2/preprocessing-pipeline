import json
from abakit.lib.Controllers.UrlController import UrlController
from abakit.lib.annotation_layer import AnnotationLayer
from abakit.atlas.VolumeMaker import VolumeMaker
from abakit.atlas.NgSegmentMaker import NgConverter
import os
import numpy as np
import json
url_id = 513
volume_id = '3cebda96f82349c4af7b7c96a171112679b665e5'
animal = 'DK73'
folder_name = f'trigeminal_demo'

controller = UrlController()
url = controller.get_urlModel(url_id)
state_json = json.loads(url.url)
layers = state_json['layers']
for layeri in layers:
    if layeri['type'] == 'annotation':
        layer = AnnotationLayer(layeri)
        volume = layer.get_annotation_with_id(volume_id)
        if volume is not None:
            break

vmaker = VolumeMaker(animal,check_path = False)
structure,contours = volume.get_volume_name_and_contours()
vmaker.set_aligned_contours({structure:contours})
vmaker.compute_COMs_origins_and_volumes()
res = vmaker.get_resolution()
segment_properties = vmaker.get_segment_properties(structures_to_include=[structure])
output_dir = os.path.join(vmaker.path.segmentation_layer,folder_name)
maker = NgConverter(volume = vmaker.volumes[structure].astype(np.uint8),scales = [res*1000,res*1000,20000],offset=list(vmaker.origins[structure]))
maker.create_neuroglancer_files(output_dir,segment_properties)