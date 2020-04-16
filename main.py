import argparse
from sqlalchemy.orm.exc import NoResultFound
from model.animal import Animal
import sys
from controller.preprocessor import SlideProcessor
from controller.spreadsheet_utilities import upload_spreadsheet, download_spreadsheet
from model.atlas_schema import manipulate_images
from sql_setup import session

def fetch_and_run(prep_id, limit, image=False, czi=False):

    slide_processor = SlideProcessor(prep_id, session)
    if czi:
        slide_processor.process_czi_dir()
    if image:
        manipulate_images(prep_id, limit)
    #slide_processor.update_tif_data()
    #slide_processor.test_tables()
    print('Finished')

def download(prep_id, session, engine):
    download_spreadsheet(prep_id, session, engine)

def upload(xlsx, session, engine):
    upload_spreadsheet(xlsx, session, engine)

if __name__ == '__main__':
    # Parsing argument
    image = False
    czi = False
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--prep_id', help='Enter the animal prep_id', required=True)
    parser.add_argument('--czi', help='Enter True to process CZI dir', required=False)
    parser.add_argument('--image', help='Enter True to manipulate images', required=False)
    parser.add_argument('--limit', help='Enter the number of TIF files to process', required=False)
    args = parser.parse_args()
    prep_id = args.prep_id
    czi = args.czi
    image = args.image
    limit = args.limit or 10000
    limit = int(limit)
    fetch_and_run(prep_id, limit, image, czi)
    #download(prep_id, session, engine)
