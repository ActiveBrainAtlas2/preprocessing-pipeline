import numpy as np
from scipy.ndimage.measurements import center_of_mass
from skimage.filters import gaussian

from library.utilities.utilities_contour import check_dict


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
        check_dict(self.COM.keys(), 'COM.keys')
        check_dict(self.volumes.keys(), 'volumes.keys')
        shared_structures = set(self.COM.keys()).intersection(self.volumes.keys())
        check_dict(shared_structures, 'shared structures')

        volume_coms = np.array([center_of_mass(self.volumes[si]) for si in shared_structures])
        average_com = np.array([self.COM[si] for si in shared_structures])
        for shared_structure in shared_structures:
            if 'SC' in shared_structure:
                com = np.array(center_of_mass(self.volumes[shared_structure]))
                avg = np.array(self.COM[shared_structure])
                print(f'{shared_structure} origin={self.COM[shared_structure]} COM={com}')
                print(f'average - volume_com = {avg - com}')
        
        average_com[np.isnan(average_com)] = 0
        volume_coms[np.isnan(volume_coms)] = 0
        origins = average_com - volume_coms
        print('origins = average_com - volume_coms', origins.dtype)
        t = np.argwhere(np.isnan(origins))
        print(f'NAN before math = {t}')
        origins = (origins - origins.min(0)) + 10
        t = np.argwhere(np.isnan(origins))
        print(f'NAN after math = {t}')
        values = [self.volumes[ki] for ki in shared_structures]
        self.volumes = dict(zip(shared_structures, values))
        return dict(zip(self.COM.keys(), origins))
    
