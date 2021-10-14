from Brain import Atlas
import numpy as np
from lib.sqlcontroller import SqlController
from FundationContourAligner import FundationContourAligner
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
