from cell_extractor.ExampleFinder import ExampleFinder 
import argparse

def calculate_one_section(animal,section,disk,segmentation_threshold):
    extractor = ExampleFinder(animal=animal,section=section,disk=disk,segmentation_threshold = segmentation_threshold)
    extractor.find_examples()
    extractor.save_examples()

if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', type=str, help='Animal ID')
    parser.add_argument('--section', type=int, help='Secton being processed')
    parser.add_argument('--disk', type=str, help='storage disk')
    args = parser.parse_args()
    animal = args.animal
    section = args.section
    disk = args.disk
    for threshold in [2100,2200,2300,2700]:
        calculate_one_section(animal,section,disk=disk,segmentation_threshold = threshold)
