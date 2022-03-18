from cell_extractor.FeatureFinder import FeatureFinder
import argparse

def calculate_one_section(animal,section,disk,segmentation_threshold):
    finder = FeatureFinder(animal,section = section,disk = disk,segmentation_threshold = segmentation_threshold)
    finder.calculate_features()
    finder.save_features()

if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', type=str, help='Animal ID')
    parser.add_argument('--section', type=int, help='Secton being processed')
    parser.add_argument('--disk', type=str, help='storage disk')
    args = parser.parse_args()
    animal = args.animal
    section = args.section
    disk = args.disk
    for threshold in [2000,3000,4000]:
        calculate_one_section(animal,section,disk=disk,segmentation_threshold = threshold)
