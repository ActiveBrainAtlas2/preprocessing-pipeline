import json
from abakit.lib.Controllers.UrlController import UrlController
from abakit.lib.annotation_layer import AnnotationLayer
from abakit.lib.Brain import Brain
from abakit.atlas.VolumeMaker import VolumeMaker
from abakit.atlas.NgSegmentMaker import NgConverter
import os
import numpy as np
import json

import cv2
from django.template import Origin
import numpy as np
from tqdm import tqdm
from scipy.ndimage.measurements import center_of_mass

volume_id = '9df3e7981321d6249c88fdada72a1230a76829bc'
controller = UrlController()
url = controller.get_urlModel(462)
state_json = json.loads(url.url)
layers = state_json['layers']
for layeri in layers:
    if layeri['type'] == 'annotation':
        layer = AnnotationLayer(layeri)
        volume = layer.get_annotation_with_id(volume_id)
        if volume is not None:
            break

vmaker = VolumeMaker()
structure,contours = volume.get_volume_name_and_contours()
vmaker.set_aligned_contours({structure:contours})
vmaker.compute_origins_and_volumes_for_all_segments()
res = [0.325,0.325,20]
segment_properties = [(1,'structure')]
folder_name = f'test'
output_dir = os.path.join(vmaker.path.segmentation_layer,folder_name)
maker = NgConverter(volume = vmaker.volumes[structure].astype(np.uint8),scales = [res*1000,res*1000,20000],offset=list(vmaker.origins[structure]))
maker.create_neuroglancer_files(output_dir,segment_properties)