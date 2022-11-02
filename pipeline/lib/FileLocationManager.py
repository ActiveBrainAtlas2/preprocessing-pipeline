import os

DATA_PATH = "/net/birdstore/Active_Atlas_Data/data_root"


class FileLocationManager(object):
    """Master class to house all file paths for preprocessing-pipeline
    All file locations are defined in this class for reference by other methods/functions.
    Default root is UCSD-specific (birdstore fileshare) but may be modified in DATA_PATH
    Subfolders to each brain are defined based on usage (some examples below):
    -czi folder [stores raw scanner images from which tiff images are extracted]
    -tif [stores full resolution images extracted from czi files]
    -neuroglancer_data [stores 'precomputed' format of entire image stack for loading into Neuroglancer visualization tool]

    Folder structure [for each brain] under DATA_ROOT will look like the following (generated with tree -L 2 -d)
    ├── czi
    ├── histogram
    │    ├── CH1
    │    ├── CH2
    │    └── CH3
    ├── neuroglancer_data
    │    ├── C1
    │    ├── C2
    │    └── C3
    ├── preps
    │    ├── CH1
    │    ├── CH2
    │    ├── CH3
    │    ├── elastix
    │    └── masks
    ├── tif
    └── www
        └── scene

    Methods in this class return a file path location based on channel (default is channel 1)
    """

    def __init__(self, stack, DATA_PATH=DATA_PATH):
        """setup the directory, file locations
        Args:
            stack: the animal brain name, AKA prep_id
        """
        self.root = os.path.join(DATA_PATH, "pipeline_data")
        self.stack = os.path.join(self.root, stack)
        self.prep = os.path.join(self.root, stack, "preps")
        self.czi = os.path.join(self.root, stack, "czi")
        self.tif = os.path.join(self.root, stack, "tif")
        self.thumbnail_original = os.path.join(self.stack, "thumbnail_original")
        self.jp2 = os.path.join(self.root, stack, "jp2")
        self.thumbnail = os.path.join(self.prep, "CH1", "thumbnail")
        self.histogram = os.path.join(self.root, stack, "histogram")
        self.thumbnail_web = os.path.join(self.root, stack, "www", "scene")
        self.neuroglancer_data = os.path.join(self.root, stack, "neuroglancer_data")
        self.neuroglancer_progress = os.path.join(self.neuroglancer_data, 'progress')
        self.brain_info = os.path.join(self.root, stack, "brains_info")
        self.operation_configs = os.path.join(self.brain_info, "operation_configs")
        self.mxnet_models = os.path.join(self.brain_info, "mxnet_models")
        self.atlas_volume = os.path.join(
            self.brain_info, "CSHL_volumes", "atlasV7", "score_volumes"
        )
        self.classifiers = os.path.join(self.brain_info, "classifiers")
        self.custom_transform = os.path.join(self.brain_info, "custom_transform")
        self.mouseatlas_tmp = os.path.join(self.brain_info, "mouseatlas_tmp")
        self.elastix_dir = os.path.join(self.prep, "elastix")
        self.full_aligned = os.path.join(self.prep, "full_aligned")
        self.masks = os.path.join(self.prep, "masks")
        self.thumbnail_masked = os.path.join(self.masks, "thumbnail_masked")
        self.thumbnail_colored = os.path.join(self.masks, "thumbnail_colored")
        self.full_masked = os.path.join(self.masks, "full_masked")
        self.rotated_and_padded_thumbnail_mask = os.path.join(
            self.masks, "thumbnail_rotated_and_padded"
        )
        self.aligned_rotated_and_padded_thumbnail_mask = os.path.join(
            self.masks, "thumbnail_aligned_rotated_and_padded"
        )
        self.shell = os.path.join(self.root, stack, "shell")

    def get_full(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "full")

    def get_thumbnail(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "thumbnail")

    def get_elastix(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "elastix")

    def get_full_cleaned(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "full_cleaned")

    def get_full_aligned(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "full_aligned")

    def get_thumbnail_aligned(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "thumbnail_aligned")

    def get_thumbnail_cleaned(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "thumbnail_cleaned")

    def get_normalized(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "normalized")

    def get_histogram(self, channel=1):
        return os.path.join(self.histogram, f"CH{channel}")

    def get_neuroglancer(self, downsample=True, channel=1, rechunck=False):
        if downsample:
            channel_outdir = f"C{channel}T"
        else:
            channel_outdir = f"C{channel}"
        if not rechunck:
            channel_outdir += "_rechunkme"
        return os.path.join(self.neuroglancer_data, f"{channel_outdir}")

    def get_neuroglancer_progress(self, downsample=True, channel=1, rechunck=False):
        if downsample:
            channel_outdir = f"C{channel}T"
        else:
            channel_outdir = f"C{channel}"
        if not rechunck:
            channel_outdir += "_rechunkme"
        return os.path.join(self.neuroglancer_progress, f"{channel_outdir}")

    def get_logdir(self):
        return os.path.join(self.stack)
