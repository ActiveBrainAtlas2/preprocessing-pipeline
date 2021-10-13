from FundationContourAligner import FundationContourAligner
from VolumeMaker import VolumeMaker
from BrainMerger import BrainMerger
animals = ['MD585', 'MD589', 'MD594']
for animal in animals:
    aligner = FundationContourAligner(animal)
    aligner.create_aligned_contours()
    # aligner.show_steps()
    aligner.save_contours()
    volumemaker = VolumeMaker(animal)
    volumemaker.compute_COMs_origins_and_volumes()
    # Volumemaker.show_results()
    volumemaker.save_coms()
    volumemaker.save_origins()
    volumemaker.save_volumes()

merger = BrainMerger()
merger.create_average_com_and_volume()
merger.save_mesh_file()
merger.save_origins()
merger.save_coms()