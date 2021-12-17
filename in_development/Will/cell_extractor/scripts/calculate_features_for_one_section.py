from cell_extractor.FeatureFinder import test_one_section
run_feature = test_one_section
import argparse
if __name__ =='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', type=str, help='Animal ID')
    parser.add_argument('--section', type=int, help='Secton being processed')
    args = parser.parse_args()
    animal = args.animal
    section = args.section
    run_feature(animal,section)