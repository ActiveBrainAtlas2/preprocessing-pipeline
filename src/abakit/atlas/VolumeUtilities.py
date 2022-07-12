import numpy as np
from scipy.ndimage.measurements import center_of_mass
from skimage.filters import gaussian


class VolumeUtilities:
        

    def gaussian_filter_volumes(self, sigma):
        for structure, volume in self.volumes.items():
            self.volumes[structure] = gaussian(volume, sigma)

    def threshold_volumes(self):
        self.thresholded_volumes = {}
        assert(hasattr(self, 'threshold'))
        assert(hasattr(self, 'volumes'))
        assert(hasattr(self, 'structures'))
        for structurei in self.structures:
            volume = self.volumes[structurei]
            if not volume[volume > 0].size == 0:
                threshold = np.quantile(volume[volume > 0], self.threshold)
            else:
                threshold = 0.5
            self.thresholded_volumes[structurei] = volume > threshold
    
    def get_origin_from_coms(self):
        assert(hasattr(self, 'COM'))
        assert(hasattr(self, 'volumes'))
        shared_structures = set(self.COM.keys()).intersection(self.volumes.keys())
        volume_coms = np.array([center_of_mass(self.volumes[si]) for si in shared_structures]).astype(int)
        average_com = np.array(list(self.COM.values()))
        origins = average_com - volume_coms
        origins = (origins - origins.min(0)).astype(int) + 10
        values = [self.volumes[ki] for ki in shared_structures]
        self.volumes = dict(zip(shared_structures,values))
        return dict(zip(self.COM.keys(), origins))
    
