'''

CREATED: 2022
LAST EDIT: 24-MAR-2022
AUTHORS: ZHONGKAI AND DUANE

DESCRIPTION:
PART OF CELL EXTRACTOR
USES FULL RESOLUTION, ALIGNED IMAGES

LOC: /Active_Atlas_Data/data_root/pipeline_data/DK55/preps/CH1/full_aligned

CREATES EXAMPLE FOR SINGLE SECTION
STEPS:
each section, turned into 10 tiles (info in: "Y:\Active_Atlas_Data\cell_segmentation\DK55\tile_info.csv")

section_id = image_id
prep_id/{channel}/{image_id}/{tiles}.tif

"Y:\Active_Atlas_Data\cell_segmentation\DK55\CH1\015\000tile-0.tif"

'''

from cell_extractor.ExampleFinder import ExampleFinder
import argparse

def calculate_one_section(animal, section, disk, segmentation_threshold):
    extractor = ExampleFinder(animal=animal, section=section, disk=disk, segmentation_threshold = segmentation_threshold)
    extractor.find_examples()
    extractor.save_examples()


def main():
    animal = 'DK55'
    section = 180
    disk = '/net/birdstore/Active_Atlas_Data/'
    for threshold in [2000, 3000, 4000]:
        calculate_one_section(animal, section, disk=disk, segmentation_threshold=threshold)


if __name__ =='__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--animal', type=str, help='Animal ID')
    # parser.add_argument('--section', type=int, help='Secton being processed')
    # parser.add_argument('--disk', type=str, help='storage disk')
    # args = parser.parse_args()
    # animal = args.animal
    # section = args.section
    # disk = args.disk

    main()


