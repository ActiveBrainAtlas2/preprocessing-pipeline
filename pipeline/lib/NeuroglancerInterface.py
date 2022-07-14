import neuroglancer
from pipeline.Controllers.SqlController import SqlController
from lib.FileLocationManager import FileLocationManager
from pathlib import Path
import SimpleITK as sitk
import numpy as np
from utilities.utilities_cvat_neuroglancer import NumpyToNeuroglancer
class NeuroglancerInterface:
    def __init__(self,dimensions):
        self.viewer = neuroglancer.Viewer()
        self.layers = {}

    def load_image_layer(self,name,image,dimensions):
        layer = neuroglancer.LocalVolume(volume_type='image',data=image, dimensions=dimensions, voxel_offset=(0, 0, 0))
        self.layers[name] = layer

    def load_annotation_layer(self,name,annotations,color,dimensions):
        layer = neuroglancer.LocalAnnotationLayer(dimensions=dimensions,annotations=annotations,annotationColor = color)
        self.layers[name] = layer
    
    def show_neuroglancer_view(self):
        with self.viewer.txn() as s:
            for name,layer in self.layers.items():
                s.layers.append(name=name,layer=layer)
        print(self.viewer)
            
class BrainViewer(NeuroglancerInterface):
    def __init__(self):
        super().__init__()
        self.thumbnail_image_cache = {}

    def get_prepi_full_aligned(prepi):
        fileMaganer = FileLocationManager(prepi)
        tif_path = fileMaganer.full_aligned
        tif_path

    def load_image(self,image_dir, spacing=None):
        """A helper function to load a directory of images as a SimpleITK Image."""
        image_dir = Path(image_dir).resolve()
        image_series = []
        for image_file in sorted(image_dir.iterdir()):
            print(f'Loading image {image_file.name}', end='\r')
            image = sitk.ReadImage(image_file.as_posix())
            image_series.append(image)
        sitk_image = sitk.JoinSeries(image_series)
        if spacing is not None:
            sitk_image.SetSpacing(spacing)
        image = sitk.GetArrayViewFromImage(sitk_image)
        image = np.swapaxes(image, 0, 2).astype('uint16')
        return image
    
    def get_prepi_thumbnail(self,prepi):
        if prepi in self.thumbnail_image_cache:
            image = self.thumbnail_image_cache[prepi]
        else:
            thumb_spacing = (10.4, 10.4, 20.0)
            data_dir = Path('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data')
            image_thumbnail_dir = data_dir / prepi / 'preps/CH1/thumbnail_aligned'
            image_16_bit = self.load_image(image_thumbnail_dir, spacing=thumb_spacing)
            image = sitk.Cast(image_16_bit, sitk.sitkFloat32)
            self.thumbnail_image_cache[prepi] = image
        return image

    def load_prepi_image(self,prepi):
        SqlController = SqlController(prepi)
        resolution = SqlController.scan_run.resolution
        dimensions = (resolution,resolution,20)
        image = self.get_prepi_thumbnail(prepi)
        self.load_image_layer(prepi,image,dimensions)
    
    def load_transfromed_prepi_image(self,prepi):
        image = self.get_prepi_thumbnail(prepi)
        transformed_image = ...
    
    def load_id_image():
        ...
