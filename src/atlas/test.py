from Brain import Atlas
import numpy as np
from lib.sqlcontroller import SqlController
from FundationContourAligner import FundationContourAligner
from Brain import Brain
from BrainMerger import BrainMerger
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama

print()
merger = BrainMerger()
merger.load_data_from_fixed_and_moving_brains()
og = merger.origins_to_merge
print()


def compare_aligned_and_unaligned_contours():
    animal = 'MD585'
    aligner = FundationContourAligner(animal)
    aligner.load_contours_for_fundation_brains()
    aligner.load_transformation_to_align_contours()
    aligner.align_contours()

    og_contours_per_str = aligner.contour_per_structure_per_section
    og_all_annotation = np.vstack([np.array(si) for ki in og_contours_per_str.values() for si in ki.values()])
    og_all_annotation.max(0)

    aligned_contour_per_str = aligner.aligned_structures
    aligned_all_annotation = np.vstack([np.array(si) for ki in aligned_contour_per_str.values() for si in ki.values()])
    aligned_all_annotation.max(0)


'MD594', 'MD585'
brain1 = Brain('MD594')
brain2 = Brain('MD585')
brain3 = Brain('MD589')
brain1.load_com()
brain2.load_com()
brain3.load_com()
brain1.load_origins()
brain2.load_origins()

brain1.compare_point_dictionaries((brain1.COM,brain2.COM))
brain1.compare_point_dictionaries((brain2.COM,brain3.COM))
brain1.compare_point_dictionaries((brain1.COM,brain3.COM))

brain1.get_image_dimension()
brain2.get_image_dimension()
brain3.get_image_dimension()

brain1.get_com_array().max(0)
brain2.get_com_array().max(0)
brain3.get_com_array().max(0)


brain1.compare_point_dictionaries((get_com(0,og),get_com(1,og)))

def get_com(braini,origin_dict):
    coms = {}
    for stri in origin_dict:
        coms[stri] = origin_dict[stri][braini]
    return coms

r, t = umeyama(brain1.get_origin_array().T, brain2.get_origin_array().T)
to = {}
for str,origin in brain1.origins.items():
    to[str] = brain_to_atlas_transform(origin, r, t)
brain1.compare_point_dictionaries((to,brain2.origins))

atlas = Atlas()
atlas.load_atlas()
print()



contours_per_str = self.aligned_contours
all_annotation = np.vstack([np.array(si) for ki in og_contours_per_str.values() for si in ki.values()])
all_annotation.max(0)

sqlcontroller = SqlController(animal)
section_size = np.array((sqlcontroller.scan_run.width, sqlcontroller.scan_run.height))

contours = [ki for ki in contour_for_structurei.values()]
maxs = np.array([np.array(ci).max(0) for ci in contours])
