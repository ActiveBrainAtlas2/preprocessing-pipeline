from collections import defaultdict
import os, sys
import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.imported_atlas_utilities import load_original_volume_all_known_structures_v3, all_known_structures_sided, \
    all_known_structures, convert_to_left_name

atlas_resolution = '10.0um'
atlas_resolution_um = 10.0
atlas_spec = dict(name='atlasV7', vol_type='score', resolution=atlas_resolution)
volumes = load_original_volume_all_known_structures_v3(atlas_spec,
                                                       structures=all_known_structures_sided)

print(all_known_structures)
volumes_mm3 = defaultdict(dict)
for name_u in all_known_structures:
    for level in np.arange(0, 1.1, .1):
        volumes_mm3[name_u][level] = np.count_nonzero(volumes[convert_to_left_name(name_u)][0] > level) * 10. ** 3 / 1e9

pd.DataFrame(volumes_mm3).to_csv('/home/eddyod/programming/pipeline_utility/neuroglancer/structure_volumes.csv')

volumes = pd.DataFrame(volumes_mm3)
print(volumes.head(100))
