from cell_extractor.FeatureFinder import test_one_section
import argparse
if __name__ =='__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--animal', type=str, help='Animal ID')
    # parser.add_argument('--section', type=int, help='Secton being processed')
    # parser.add_argument('--disk', type=str, help='storage disk')
    # args = parser.parse_args()
    # animal = args.animal
    # section = args.section
    # disk = args.disk
    # test_one_section(animal,section)
    test_one_section('DK46',90,disk = 'scratch')