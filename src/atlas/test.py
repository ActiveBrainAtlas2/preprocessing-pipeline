from Brain import Atlas
import numpy as np
from lib.sqlcontroller import SqlController
from FundationContourAligner import FundationContourAligner
from Brain import Brain
from BrainMerger import BrainMerger
from abakit.registration.algorithm import brain_to_atlas_transform, umeyama
class Debugger(Brain):
    def __init__(self):
        self.brains = ['MD594', 'MD585','MD589']
        self.brains = [Brain(braini) for braini in self.brains]
        for braini in self.brains:
            braini.load_volumes()
            braini.load_com()
            braini.load_origins()
            braini.load_origins()
            braini.load_aligned_contours()

    def plot_structure_stacks(self):
        for braini in self.brains:
            braini.plot_volume_stack()

    def debug_brain_merger(self):
        merger = BrainMerger()
        merger.load_data_from_fixed_and_moving_brains()
        og = merger.origins_to_merge
        merger.plotter.compare_point_dictionaries((merger.fixed_brain.origins,merger.moving_brains[0].transformed_origins))
        self.plotter.compare_point_dictionaries((self.get_com(0,og),self.get_com(1,og)))
        self.plotter.compare_point_dictionaries((self.get_com(0,og),self.get_com(1,og)))


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

    def compare_coms(self):
        brain1,brain2,brain3 = self.brains
        brain1.compare_point_dictionaries((brain1.COM,brain2.COM))
        brain1.compare_point_dictionaries((brain2.COM,brain3.COM))
        brain1.compare_point_dictionaries((brain1.COM,brain3.COM))

    def get_image_dimensions(self):
        return [braini.get_image_dimension() for braini in self.brains]

    def get_com_max(self):
        return [braini.get_com_array().max(0) for braini in self.brains]
        
    def get_com(braini,origin_dict):
        coms = {}
        for stri in origin_dict:
            coms[stri] = origin_dict[stri][braini]
        return coms

    def test_transformation(self):
        brain1,brain2,brain3 = self.brains
        r, t = umeyama(brain1.get_origin_array().T, brain2.get_origin_array().T)
        to = {}
        for str,origin in brain1.origins.items():
            to[str] = brain_to_atlas_transform(origin, r, t)
        brain1.compare_point_dictionaries((to,brain2.origins))

    def unorganized(self):
        atlas = Atlas()
        atlas.load_atlas()
        contours_per_str = self.aligned_contours
        all_annotation = np.vstack([np.array(si) for ki in og_contours_per_str.values() for si in ki.values()])
        all_annotation.max(0)
        sqlcontroller = SqlController(animal)
        section_size = np.array((sqlcontroller.scan_run.width, sqlcontroller.scan_run.height))
        contours = [ki for ki in contour_for_structurei.values()]
        maxs = np.array([np.array(ci).max(0) for ci in contours])

if __name__ == '__main__':
    debugger = Debugger()
    debugger.brains[0].compare_structure_vs_contour()
    debugger.plot_structure_stacks()