import argparse
import jinja2
import os, sys

HOME = os.path.expanduser("~")
DIR = os.path.join(HOME, 'programming/pipeline_utility')
sys.path.append(DIR)

from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager

def make_pages(animal, fetch, layer):
    templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
    templateEnv = jinja2.Environment(loader=templateLoader)
    if 'sql' in fetch:
        sqlController = SqlController(animal)
        valid_sections = sqlController.get_sections(animal, 1)
        container = "container.html"
    else:
        fileLocationManager = FileLocationManager(animal)
        valid_sections = sorted(os.listdir(fileLocationManager.thumbnail_web))
        container = "list_dir.html"

    if layer is not None:
        fileLocationManager = FileLocationManager(animal)
        INPUT = os.path.join(fileLocationManager.thumbnail_web, 'points', layer)
        valid_sections = sorted(os.listdir(INPUT))
        container = "list_points.html"
        template = templateEnv.get_template(container)
        lfiles = len(valid_sections)
        outputText = template.render(animal=animal, valid_sections=valid_sections, lfiles=lfiles, layer=layer)
    else:
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
    parser.add_argument('--fetch', help='Enter sql or dir', required=False, default='sql')
    parser.add_argument('--layer', help='Enter layer', required=False)
    args = parser.parse_args()
    animal = args.animal
    fetch = args.fetch
    layer = args.layer
    make_pages(animal, fetch, layer)
