import argparse
import jinja2
import os, sys

sys.path.append(os.path.join(os.getcwd(), '../../'))
from utilities.sqlcontroller import SqlController

def make_pages(animal):
    sqlController = SqlController()
    sqlController.get_animal_info(animal)
    valid_sections = sqlController.get_raw_sections(animal)
    templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    container = "container.html"
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
