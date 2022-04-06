"""
This is the base sql class. It is mostly used per animal, so the init function
needs an animal passed to the constructor
It also needs for the animal, histology and scan run tables to be
filled out for each animal to use
"""
import sys
from lib.sql_setup import session, pooledsession
from model.urlModel import UrlModel
from model.task import Task, ProgressLookup
from model.annotations_points import AnnotationPoint
from model.brain_region import BrainRegion
from model.brain_shape import BrainShape
from model.slide_czi_to_tif import SlideCziTif
from model.slide import Slide
from model.section import Section
from model.scan_run import ScanRun
from model.histology import Histology
from model.animal import Animal
from model.elastix_transformation import ElastixTransformation
from model.file_log import FileLog
import json
import pandas as pd
from collections import OrderedDict
from datetime import datetime
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
import binascii
import os


class SqlController(object):
    """ Create a class for processing the pipeline,
    """

    def __init__(self, animal):
        """ setup the attributes for the SlidesProcessor class
            Args:
                animal: object of animal to process
        """
        self.session = session
        try:
            self.animal = self.session.query(Animal).filter(
                Animal.prep_id == animal).one()
        except NoResultFound:
            print(f'No animal/brain with the name {animal} was found in the database.')
            sys.exit()
        try:
            self.histology = self.session.query(Histology).filter(
                Histology.prep_id == animal).one()
        except NoResultFound:
            print(f'No histology for {animal}')
        try:
            self.scan_run = self.session.query(ScanRun).filter(
                ScanRun.prep_id == animal).order_by(ScanRun.id.desc()).one()
        except NoResultFound:
            print(f'No scan run for {animal}')
        self.slides = None
        self.tifs = None
        self.valid_sections = OrderedDict()
        # fill up the metadata_cache variable
        # self.session.close()
    
    def animal_exists(self,animal):
        return bool(self.session.query(Animal).filter(Animal.prep_id == animal).first())

    def slide_exists(self,scan_id,slide_id):
        return bool(self.session.query(Slide).filter(Slide.scan_run_id == scan_id).filter(Slide.slide_physical_id == slide_id).first())

    def get_animal_list(self):
        results = self.session.query(Animal).all()
        animals = []
        for resulti in results:
            animals.append(resulti.prep_id)
        return animals
    
    def get_annotated_animals(self):
        results = self.session.query(AnnotationPoint)\
            .filter(AnnotationPoint.FK_input_id == 1)\
            .filter(AnnotationPoint.FK_owner_id == 2)\
            .filter(AnnotationPoint.label == 'COM').all()
        return np.unique([ri.prep_id for ri in results])

    def get_values_from_column(self, query_result):
        query_result = query_result.all()
        query_result = [entryi[0] for entryi in query_result]
        return query_result

    def get_section(self, ID):
        """
        The sections table is a view and it is already filtered by active and file_status = 'good'
        This qeury returns a single section by id.
        Args:
            id: integer primary key

        Returns: one section
        """
        return self.session.query(Section).filter(Section.id == ID).one()

    def get_slide(self, ID):
        """
        Args:
            id: integer primary key

        Returns: one slide
        """
        return self.session.query(Slide).filter(Slide.id == ID).one()

    def get_tif(self, ID):
        """
        Args:
            id: integer primary key

        Returns: one tif
        """
        return self.session.query(SlideCziTif).filter(SlideCziTif.id == ID).one()

    def get_urlModel(self, ID):
        """
        Args:
            id: integer primary key

        Returns: one neuroglancer json object
        """
        return self.session.query(UrlModel).filter(UrlModel.id == ID).one()

    def get_url_id_list(self):
        urls = self.session.query(UrlModel).all()
        ids = [url.id for url in urls]
        return ids

    def get_sections(self, animal, channel):
        """
        The sections table is a view and it is already filtered by active and file_status = 'good'
        The ordering is important. This needs to come from the histology table.
        Args:
            animal: the animal to query
            channel: 1 or 2 or 3.

        Returns: list of sections in order

        """
        orderby = self.histology.side_sectioned_first

        if orderby == 'DESC':
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .order_by(Section.slide_physical_id.desc())\
                .order_by(Section.scene_number.desc()).all()
        else:
            sections = self.session.query(Section).filter(Section.prep_id == animal)\
                .filter(Section.channel == channel)\
                .order_by(Section.slide_physical_id.asc())\
                .order_by(Section.scene_number.asc()).all()

        return sections

    def get_distinct_section_filenames(self, animal, channel):
        """
        Very similar to the get_sections query but this will return a list of
        distinct file names. Since some of the scenes get duplicated in the QA process,
        we need to get the tifs without duplicates. The duplicates will then get replicated
        with the get_sections method. The order doesn't matter here.
        Args:
            animal: the animal to query
            channel: 1 or 2 or 3.

        Returns: list of sections with distinct file names

        """
        sections = self.session.query(Section.czi_file, Section.file_name, Section.scene_index,  Section.channel_index).distinct()\
            .filter(Section.prep_id == animal).filter(
            Section.channel == channel).all()

        return sections

    def get_slide_czi_to_tifs(self, channel):
        slides = self.session.query(Slide).filter(Slide.scan_run_id == self.scan_run.id)\
            .filter(Slide.slide_status == 'Good').all()
        slide_czi_to_tifs = self.session.query(SlideCziTif).filter(SlideCziTif.channel == channel)\
            .filter(SlideCziTif.slide_id.in_([slide.id for slide in slides]))\
            .filter(SlideCziTif.active == 1).all()

        return slide_czi_to_tifs

    def update_row(self, row):
        try:
            self.session.merge(row)
            self.session.commit()
        except Exception as e:
            print(f'No merge for  {e}')
            self.session.rollback()

    def update_scanrun(self, id):
        width = self.session.query(func.max(SlideCziTif.width)).join(Slide).join(ScanRun)\
            .filter(SlideCziTif.active == True) \
            .filter(ScanRun.id == id).scalar()
        height = self.session.query(func.max(SlideCziTif.height)).join(Slide).join(ScanRun)\
            .filter(SlideCziTif.active == True) \
            .filter(ScanRun.id == id).scalar()
        SAFEMAX = 10000
        LITTLE_BIT_MORE = 500
        # just to be safe, we don't want to update numbers that aren't realistic
        if height > SAFEMAX and width > SAFEMAX:
            height = round(height, -3)
            width = round(width, -3)
            height += LITTLE_BIT_MORE
            width += LITTLE_BIT_MORE
            # width and height get flipped
            try:
                self.session.query(ScanRun).filter(ScanRun.id == id).update(
                    {'width': height, 'height': width})
                self.session.commit()
            except Exception as e:
                print(f'No merge for  {e}')
                self.session.rollback()

    def update_tif(self, id, width, height):
        try:
            self.session.query(SlideCziTif).filter(
                SlideCziTif.id == id).update({'width': width, 'height': height})
            self.session.commit()
        except Exception as e:
            print(f'No merge for  {e}')
            self.session.rollback()

    def get_sections_numbers(self, animal):
        sections = self.session.query(Section).filter(
            Section.prep_id == animal).filter(Section.channel == 1).all()

        section_numbers = []
        for i, r in enumerate(sections):
            section_numbers.append(i)

        return section_numbers

    def get_sections_dict(self, animal):
        sections = self.session.query(Section).filter(
            Section.prep_id == animal).filter(Section.channel == 1).all()

        sections_dict = {}
        for i, r in enumerate(sections):
            sections_dict[i] = str(i).zfill(3) + 'tif'

        return sections_dict

    def get_structure(self, abbrv):
        """
        Returns a structure
        This search has to be case sensitive!
        :param abbrv: the abbreviation of the structure
        :return: structure object
        """
        return self.session.query(BrainRegion).filter(BrainRegion.abbreviation == func.binary(abbrv)).one()
    
    def get_annotation_points(self,search_dictionary):
        query_start = self.session.query(AnnotationPoint)
        for key, value in search_dictionary.items():
            query_start = eval(f'query_start.filter(AnnotationPoint.{key}=="{value}")')
        return self.get_coordinates_from_query_result(query_start.all())


    def get_distinct_structures(self, label):
        """
        Get list of distinct structures in a layer. Used mostly for recreating atlas
        Args:
            label: the label/layer to query

        Returns: list of structure IDs

        """
        ids = []
        
        for FK_structure_id in self.session.query(AnnotationPoint.FK_structure_id).distinct():
            ids.append(FK_structure_id[0])

        return ids

    def get_distinct_labels(self, animal):
        '''
        Query the polygon data from the foundation brains. We want all the data
        that was imported from the CSV files for each animal
        INFO: 
            54 is the id for polygons
            52 everything below 52 is an Atlas brain region
        :param animal: AKA prep_id, string for animal name
        '''
        labels = []
        subquery = self.session.query(BrainRegion.abbreviation).filter(BrainRegion.id < 52).subquery()
        query = self.session.query(AnnotationPoint.label)\
            .filter(AnnotationPoint.label.in_(subquery))\
            .filter(AnnotationPoint.prep_id==animal)\
            .filter(AnnotationPoint.FK_structure_id==54)\
            .order_by(AnnotationPoint.label.asc())\
            .distinct()
        
        for label in query:
            labels.append(label[0])
            
        return labels

    def get_coordinates_from_query_result(self,query_result):
        coord = []
        resolution = self.scan_run.resolution
        for resulti in query_result:
            coord.append([resulti.x/resolution,resulti.y/resolution,int(resulti.section/20)])
        return(np.array(coord))

    def get_structure_color(self, abbrv):
        """
        Returns a color code as int
        This search has to be case sensitive!
        :param abbrv: the abbreviation of the structure
        :return: tuple of rgb
        """
        row = self.session.query(BrainRegion).filter(
            BrainRegion.abbreviation == func.binary(abbrv)).one()
        return int(row.color)

    def get_structure_from_id(self, FK_structure_id):
        """
        Sometimes you need the abbr from the ID
        """
        row = self.session.query(BrainRegion).filter(
            BrainRegion.id == func.binary(FK_structure_id)).one()
        return row.abbreviation

    def get_structure_color_rgb(self, abbrv):
        """
        Returns a color code in RGB format like (1,2,3)
        This search has to be case sensitive!
        :param abbrv: the abbreviation of the structure
        :return: tuple of rgb
        """
        row = self.session.query(BrainRegion).filter(
            BrainRegion.abbreviation == func.binary(abbrv)).one()
        hexa = row.hexadecimal
        h = hexa.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def get_structures(self):
        return self.session.query(BrainRegion).filter(BrainRegion.active.is_(True)).all()

    def get_structures_dict(self):
        rows = self.session.query(BrainRegion)\
            .filter(BrainRegion.abbreviation != 'R')\
            .filter(BrainRegion.is_structure ==1).filter(
            BrainRegion.active.is_(True)).all()
        structures_dict = {}
        for structure in rows:
            structures_dict[structure.abbreviation] = [
                structure.description, structure.color, structure.id]

        return structures_dict

    def get_structures_list(self):
        rows = self.session.query(BrainRegion).filter(BrainRegion.id<52)\
                .filter(BrainRegion.abbreviation != 'R').filter(BrainRegion.active.is_(
            True)).order_by(BrainRegion.abbreviation.asc()).all()
        structures = []
        for structure in rows:
            structures.append(structure.abbreviation)

        return structures

    def get_sided_structures(self):
        """
        Not sure when/if this is needed, but will only return sided structures
        :return: list of structures that are not singules
        """
        rows = self.session.query(BrainRegion).filter(
            BrainRegion.active.is_(True)).all()
        structures = []
        for structure in rows:
            if "_" in structure.abbreviation:
                structures.append(structure.abbreviation)

        return sorted(structures)

    def get_section_count(self, animal):
        try:
            count = self.session.query(Section).filter(Section.prep_id == animal).filter(Section.channel == 1).count()
        except:
            count = 0
        return count

    def get_current_task(self, animal):
        step = None
        try:
            lookup_id = self.session.query(func.max(Task.lookup_id)).filter(Task.prep_id == animal) \
                .filter(Task.completed.is_(True)).scalar()
        except NoResultFound as nrf:
            print('No results for {} error: {}'.format(animal, nrf))
            return step

        try:
            lookup = self.session.query(ProgressLookup).filter(
                ProgressLookup.id == lookup_id).one()
        except NoResultFound as nrf:
            print('Bad lookup code for {} error: {}'.format(lookup_id, nrf))
            return step

        return lookup.description

    def set_task(self, animal, lookup_id):
        """
        Look up the lookup up from the step. Check if the animal already exists,
        if not, insert, otherwise, update
        Args:
            animal: string of the animal you are working on
            lookup_id: current lookup ID
        Returns:
            nothing, just merges
        """
        try:
            lookup = self.session.query(ProgressLookup) \
                .filter(ProgressLookup.id == lookup_id) \
                .limit(1).one()
        except NoResultFound:
            print('No lookup for {} so we will enter one.'.format(lookup_id))
        try:
            task = self.session.query(Task).filter(Task.lookup_id == lookup.id) \
                .filter(Task.prep_id == animal).one()
        except NoResultFound:
            print('No step for {}, so creating new task.'.format(lookup_id))
            task = Task(animal, lookup.id, True)

        try:
            self.session.merge(task)
            self.session.commit()
        except:
            print('Bad lookup code for {}'.format(lookup.id))
            self.session.rollback()
    
    def structure_abbreviation_to_id(self,abbreviation):
        try:
            structure = self.get_structure(str(abbreviation).strip())
        except NoResultFound as nrf:
            print(f'No structure found for {abbreviation} {nrf}')
            return
        return structure.id

    def get_com_dict(self, prep_id, FK_input_id=1, person_id=2):
        return self.get_annotation_points_entry(prep_id=prep_id, FK_input_id=FK_input_id, \
             person_id=person_id, label='COM')
    
    def get_annotation_points_entry(self, prep_id, FK_input_id=1, person_id=2, label='COM'):
        rows = self.session.query(AnnotationPoint)\
            .filter(AnnotationPoint.prep_id == prep_id)\
            .filter(AnnotationPoint.FK_input_id == FK_input_id)\
            .filter(AnnotationPoint.FK_owner_id == person_id)\
            .filter(AnnotationPoint.label == label)\
            .all()
        row_dict = {}
        for row in rows:
            structure = row.brain_region.abbreviation
            row_dict[structure] = [row.x, row.y, row.z]
        return row_dict
    
    def get_annotations(self, prep_id, input_id, label):
        rows = self.session.query(AnnotationPoint)\
            .filter(AnnotationPoint.prep_id == prep_id)\
            .filter(AnnotationPoint.FK_input_id == input_id)\
            .filter(AnnotationPoint.label == label)\
            .all()
        return rows
    
    def get_annotations_by_structure(self, prep_id, input_type_id, label, FK_structure_id):
        rows = self.session.query(AnnotationPoint)\
            .filter(AnnotationPoint.prep_id == prep_id)\
            .filter(AnnotationPoint.FK_input_id == input_type_id)\
            .filter(AnnotationPoint.label == label)\
            .filter(AnnotationPoint.FK_structure_id==FK_structure_id)\
            .all()
        return rows
    
    def get_structure_min_max(self, prep_id, label, FK_structure_id):
        values = self.session.query(
            func.min(AnnotationPoint.x),
            func.max(AnnotationPoint.x),
            func.min(AnnotationPoint.y),
            func.max(AnnotationPoint.y),
            func.min(AnnotationPoint.z),
            func.max(AnnotationPoint.z))\
                .filter(AnnotationPoint.prep_id == prep_id)\
                .filter(AnnotationPoint.label == label)\
                .filter(AnnotationPoint.FK_structure_id == FK_structure_id).all() 
        
        minx = values[0][0]
        maxx = values[0][1]
        miny = values[0][2]
        maxy = values[0][3]
        minz = values[0][4]
        maxz = values[0][5]
        return minx, maxx, miny, maxy, minz, maxz

    def get_brain_shape(self, prep_id, FK_structure_id, transformed):
        try:
            brain_shape = self.session.query(BrainShape)\
                                .filter(BrainShape.prep_id == prep_id)\
                                .filter(BrainShape.FK_structure_id == FK_structure_id)\
                                .filter(BrainShape.transformed == transformed)\
                                .one()
        except NoResultFound:
            print(f'No brain shape for {prep_id} structure ID {FK_structure_id}')
            brain_shape = None
        return brain_shape


    def get_atlas_centers(self):
        PERSON_ID_LAUREN = 16
        INPUT_TYPE_MANUAL = 1
        return self.get_com_dict('Atlas',INPUT_TYPE_MANUAL,PERSON_ID_LAUREN)

    def get_point_dataframe(self, id):
        """
        :param id: primary key from the url. Look at:
         https://activebrainatlas.ucsd.edu/activebrainatlas/admin/neuroglancer/points/164/change/
         for example use 164 for the primary key
         to get the ID
        :return: a pandas dataframe
        """

        try:
            urlModel = self.session.query(
                UrlModel).filter(UrlModel.id == id).one()
        except NoResultFound as nrf:
            print('Bad ID for {} error: {}'.format(id, nrf))
            return

        result = None
        dfs = []
        if urlModel.url is not None:
            json_txt = json.loads(urlModel.url)
            labels = json_txt['labels']
            for l in labels:
                if 'annotations' in l:
                    name = l['name']
                    annotation = l['annotations']
                    d = [row['point'] for row in annotation]
                    df = pd.DataFrame(d, columns=['X', 'Y', 'Section'])
                    df['X'] = df['X'].astype(int)
                    df['Y'] = df['Y'].astype(int)
                    df['Section'] = df['Section'].astype(int)
                    df['label'] = name
                    df = df[['label', 'X', 'Y', 'Section']]
                    dfs.append(df)
            if len(dfs) == 0:
                result = None
            elif len(dfs) == 1:
                result = dfs[0]
            else:
                result = pd.concat(dfs)

        return result

    def get_progress_id(self, downsample, channel, action):

        try:
            lookup = self.session.query(ProgressLookup) \
                .filter(ProgressLookup.downsample == downsample) \
                .filter(ProgressLookup.channel == channel) \
                .filter(ProgressLookup.action == action).one()
        except NoResultFound as nrf:
            print(
                f'Bad lookup code for {downsample} {channel} {action} error: {nrf}')
            return 0

        return lookup.id

    def check_elastix_row(self, animal, section):
        row_exists = bool(self.session.query(ElastixTransformation).filter(
            ElastixTransformation.prep_id == animal,
            ElastixTransformation.section == section).first())
        return row_exists

    def add_row(self, data):
        try:
            self.session.add(data)
            self.session.commit()
        except Exception as e:
            print(f'No merge {e}')
            self.session.rollback()
        finally:
            self.session.close()
        
    def add_url(self,content,title,person_id):
        url = UrlModel(url = content,comments = title,person_id = person_id)
        self.add_row(url)

    def delete_url(self,title,person_id):
        self.session.query(UrlModel)\
            .filter(UrlModel.comments == title)\
            .filter(UrlModel.person_id == person_id).delete()
        self.session.commit()

    def add_elastix_row(self, animal, section, rotation, xshift, yshift):
        data = ElastixTransformation(
            prep_id=animal, section=section, rotation=rotation, xshift=xshift, yshift=yshift,
            created=datetime.utcnow(), active=True)
        self.add_row(data)

    def add_annotation_point_row(self, animal, owner_id, input_id, coordinates, structure_id, label, ordering=0, segment_id=None):
        x, y, z = coordinates
        data = AnnotationPoint(prep_id=animal, FK_owner_id=owner_id, FK_input_id=input_id, x=x, y=y, \
            z=z, FK_structure_id=structure_id, label=label, ordering=ordering, segment_id=segment_id)
        self.add_row(data)
    
    def add_com(self, prep_id, abbreviation, coordinates, person_id=2 , input_id = 1):
        structure_id = self.structure_abbreviation_to_id(abbreviation)
        if self.annotation_points_row_exists(animal=prep_id,person_id = person_id,input_id = input_id,\
            structure_id = structure_id,label = 'COM'):
            self.delete_annotation_points_row(animal=prep_id,person_id = person_id,input_id = input_id,\
                structure_id = structure_id,label = 'COM')
        self.add_annotation_points_row(animal = prep_id,person_id = person_id,input_id = input_id,\
            coordinates = coordinates,structure_id = structure_id,label = 'COM')
    
    def url_exists(self,comments):
        row_exists = bool(self.session.query(UrlModel).filter(UrlModel.comments == comments).first())
        return row_exists

    def annotation_points_row_exists(self,animal, person_id, input_id, structure_id, label):
        row_exists = bool(self.session.query(AnnotationPoint).filter(
            AnnotationPoint.prep_id == animal, 
            AnnotationPoint.FK_owner_id == person_id, 
            AnnotationPoint.FK_input_id == input_id, 
            AnnotationPoint.FK_structure_id == structure_id,
            AnnotationPoint.label == label).first())
        return row_exists
    
    def get_new_segment_id(self):
        new_id = binascii.b2a_hex(os.urandom(20)).decode('ascii')
        used_ids = [i.segment_id for i in self.session.query(AnnotationPoint.polygon_id).distinct().all()]
        while new_id in used_ids:
            new_id = binascii.b2a_hex(os.urandom(20)).decode('ascii')
        return new_id
 
    def delete_annotation_points_row(self,animal,person_id,input_id,structure_id,label):
        self.session.query(AnnotationPoint)\
            .filter(AnnotationPoint.prep_id == animal)\
            .filter(AnnotationPoint.FK_input_id == input_id)\
            .filter(AnnotationPoint.FK_owner_id == person_id)\
            .filter(AnnotationPoint.FK_structure_id == structure_id)\
            .filter(AnnotationPoint.label == label).delete()
        self.session.commit()

    def clear_elastix(self, animal):
        self.session.query(ElastixTransformation).filter(ElastixTransformation.prep_id == animal)\
            .delete()

    def convert_coordinate_pixel_to_microns(self,coordinates):
        resolution = self.scan_run.resolution
        self.session.close()
        x,y,z = coordinates
        x*=resolution
        y*=resolution
        z*=20
        return x,y,z

def file_processed(animal, progress_id, filename):
    """
    Args:
        animal: prep_id
        progress_id: ID from progress_lookup table
        filename: filename you are working on
    Returns:
        boolean if file exists or not
    """
    try:
        file_log = pooledsession.query(FileLog) \
            .filter(FileLog.prep_id == animal) \
            .filter(FileLog.progress_id == progress_id) \
            .filter(FileLog.filename == filename).one()
    except NoResultFound as nrf:
        return False
    finally:
        pooledsession.close()

    return True

def set_file_completed(animal, progress_id, filename):
    """
    Args:
        animal: prep_id
        progress_id: ID from progress_lookup table
        filename: filename you are working on
    Returns:
        nothing, just merges
    """

    file_log = FileLog(prep_id=animal, progress_id=progress_id, filename=filename,
                       created=datetime.utcnow(), active=True)

    try:
        pooledsession.add(file_log)
        pooledsession.commit()
    except Exception as e:
        print(f'No merge for {animal} {filename} {e}')
        pooledsession.rollback()
    finally:
        pooledsession.close()


    

