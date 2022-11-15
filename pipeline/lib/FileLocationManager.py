"""This module takes care of all the file locations of all the czi, tiff and log files.
"""
import os

data_path = "/net/birdstore/Active_Atlas_Data/data_root"


class FileLocationManager(object):
    """Master class to house all file paths for preprocessing-pipeline

    All file locations are defined in this class for reference by other methods/functions.
    Default root is UCSD-specific (birdstore fileshare) but may be modified in data_path
    Subfolders to each brain are defined based on usage (some examples below):
    -czi folder [stores raw scanner images from which tiff images are extracted]
    -tif [stores full resolution images extracted from czi files]
    -neuroglancer_data [stores 'precomputed' format of entire image animal for loading into Neuroglancer visualization tool]


    """

    def __init__(self, animal, data_path=data_path):
        """setup the directory, file locations
        Args:
            animal: the animal brain name, AKA prep_id
        """
        self.root = os.path.join(data_path, "pipeline_data")
        self.animal = os.path.join(self.root, animal)
        self.prep = os.path.join(self.root, animal, "preps")
        self.czi = os.path.join(self.root, animal, "czi")
        self.tif = os.path.join(self.root, animal, "tif")
        self.thumbnail_original = os.path.join(self.animal, "thumbnail_original")
        self.jp2 = os.path.join(self.root, animal, "jp2")
        self.thumbnail = os.path.join(self.prep, "CH1", "thumbnail")
        self.histogram = os.path.join(self.root, animal, "histogram")
        self.thumbnail_web = os.path.join(self.root, animal, "www", "scene")
        self.neuroglancer_data = os.path.join(self.root, animal, "neuroglancer_data")
        self.neuroglancer_progress = os.path.join(self.neuroglancer_data, 'progress')
        self.brain_info = os.path.join(self.root, animal, "brains_info")
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

    def get_full(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "full")

    def get_thumbnail(self, channel=1):
        return os.path.join(self.prep, f"CH{channel}", "thumbnail")

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
        '''
        Returns path to store neuroglancer files ('precomputed' format)

        Note: This path is also web-accessbile [@ UCSD]
        '''
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
        '''
        This method is only called on first instance then stored as environment variable
        [See: FileLogger class for more information]
        '''
        return os.path.join(self.animal)
