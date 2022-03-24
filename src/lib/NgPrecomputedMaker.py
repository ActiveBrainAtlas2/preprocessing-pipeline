import os
from concurrent.futures.process import ProcessPoolExecutor
from skimage import io
from lib.utilities_cvat_neuroglancer import NumpyToNeuroglancer, calculate_chunks
from lib.SqlController import SqlController
from lib.utilities_process import get_cpus, SCALING_FACTOR, test_dir

class NgPrecomputedMaker:
    def get_scales(self):
        self.sqlController = SqlController(self.animal)
        db_resolution = self.sqlController.scan_run.resolution
        resolution = int(db_resolution * 1000 / SCALING_FACTOR)
        if not self.downsample:
            resolution = int(db_resolution * 1000)
        scales = (resolution, resolution, 20000)
        return scales

    def get_file_information(self,INPUT):
        files = sorted(os.listdir(INPUT))
        midpoint = len(files) // 2
        midfilepath = os.path.join(INPUT, files[midpoint])
        midfile = io.imread(midfilepath, img_num=0)
        height = midfile.shape[0]
        width = midfile.shape[1]
        num_channels = midfile.shape[2] if len(midfile.shape) > 2 else 1
        file_keys = []
        volume_size = (width, height, len(files))
        for i, f in enumerate(files):
            filepath = os.path.join(INPUT, f)
            file_keys.append([i,filepath])
        return midfile,file_keys,volume_size,num_channels

    def create_neuroglancer(self):
        INPUT = self.fileLocationManager.get_thumbnail_aligned(channel=self.channel)
        progress_id = self.sqlController.get_progress_id(self.downsample, self.channel, 'NEUROGLANCER')
        self.sqlController.session.close()
        if not self.downsample:
            INPUT = self.fileLocationManager.get_full_aligned(channel=self.channel)
            self.sqlController.set_task(self.animal, progress_id)
        OUTPUT_DIR = self.fileLocationManager.get_neuroglancer(self.downsample,self.channel)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        test_dir(self.animal, INPUT, self.downsample, same_size=True)
        midfile,file_keys,volume_size,num_channels = self.get_file_information(INPUT)
        chunks = calculate_chunks(self.downsample, -1)
        scales = self.get_scales()
        ng = NumpyToNeuroglancer(self.animal, None, scales, 'image', midfile.dtype, num_channels=num_channels, chunk_size=chunks)
        ng.init_precomputed(OUTPUT_DIR, volume_size, progress_id=progress_id)
        workers, _ = get_cpus()
        with ProcessPoolExecutor(max_workers=workers) as executor:
            if num_channels == 1:
                executor.map(ng.process_image, sorted(file_keys))
            else:
                executor.map(ng.process_3channel, sorted(file_keys))
        ng.precomputed_vol.cache.flush()

    def create_neuroglancer_lite(self,INPUT,OUTPUT_DIR):
        scales = self.get_scales('DK39',self.downsample)
        midfile,file_keys,volume_size,num_channels = self.get_file_information(INPUT)
        chunks = calculate_chunks(self.downsample, -1)
        ng = NumpyToNeuroglancer('Atlas', None, scales, 'image', midfile.dtype, num_channels=num_channels, chunk_size=chunks)
        ng.init_precomputed(OUTPUT_DIR, volume_size, progress_id=None)
        with ProcessPoolExecutor(max_workers=10) as executor:
            executor.map(ng.process_image, sorted(file_keys))