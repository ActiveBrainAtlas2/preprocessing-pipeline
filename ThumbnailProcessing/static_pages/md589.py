import argparse
import jinja2
import os, sys

sys.path.append(os.path.join(os.getcwd(), '../../'))

def make_pages(animal):
    templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    valid_sections = sorted(os.listdir('/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/MD589/preps/CH1/r_rmc_vta'))
    container = "list_dir.html"

    template = templateEnv.get_template(container)
    lfiles = len(valid_sections)
    outputText = template.render(animal=animal, valid_sections=valid_sections, lfiles=lfiles)  # this is where to put args to the template renderer

    # to save the results
    filename = '{}.thumbnails.html'.format(animal)
    with open(filename, "w") as fh:
        fh.write(outputText)

if __name__ == '__main__':
    # Parsing argument
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    make_pages(animal)
