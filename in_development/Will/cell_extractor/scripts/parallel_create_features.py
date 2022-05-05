from cell_extractor.FeatureFinder import create_features_for_all_sections 
import argparse

if __name__ =='__main__':
    animal = 'DK52'
    create_features_for_all_sections(animal,disk = '/net/birdstore/Active_Atlas_Data/',segmentation_threshold=2000)
