from cell_extractor.BorderFinder import BorderFinder
from cell_extractor.CellDetectorBase import CellDetectorBase
from cell_extractor.utils import numpy_to_json,create_QC_url
from Controllers.SqlController import SqlController
from cell_extractor.InterRatorResults import Round3DK41MarissaJulianResult,Round4DK41MarissaJulianResult,get_beth_positive_marking_for_DK41
from cell_extractor.utils import get_ids_in_subcategory
import pandas as pd

class QcGenerater:
    def __init__(self,animal,round):
        self.animal = animal
        self.round = round
        self.load_detections()
        self.eliminate_border_cells()
        self.eliminate_duplicate_sections()
        self.controller = SqlController(animal)
    
    def load_detections(self):
        detector = CellDetectorBase(self.animal,round = self.round,segmentation_threshold=2000)
        self.detections = detector.load_detections()
        self.detections = self.detections[self.detections>=0]

    def get_sure_and_unsure_cells(self,sure_and_unsure_sample):
        sure = self.detections[self.detections.predictions==2]
        unsure = self.detections[self.detections.predictions==0]
        sure.rename(columns = {'x' : 'col', 'y' : 'row'}, inplace = True)
        unsure.rename(columns = {'x' : 'col', 'y' : 'row'}, inplace = True)
        sure_data = sure[['col','row','section']].sample(sure_and_unsure_sample[0]).sort_values('section').to_numpy().tolist()
        unsure_data = unsure[['col','row','section']].sample(sure_and_unsure_sample[1]).sort_values('section').to_numpy().tolist()
        sure_cells = numpy_to_json(sure_data,category = f'Round{round+1}_Sure')
        unsure_cells = numpy_to_json(unsure_data,color_hex='#1d66db',category = f'Round{round+1}_Unsure')
        return sure_cells,unsure_cells

    def eliminate_border_cells(self):
        finder = BorderFinder(self.animal)
        _,self.detections = finder.find_border_cells(self.detections)
    
    def eliminate_duplicate_sections(self):
        duplicate_sections = self.controller.get_duplicate_sections()
        self.detections = self.detections[[i not in duplicate_sections for i in self.detections.section]]

class QcGeneraterDK41(QcGenerater):
    def __init__(self,round):
        super().__init__('DK41',round)
        self.elimincate_existing_annotations()

    def elimincate_existing_annotations(self):
        inter_rator = Round3DK41MarissaJulianResult()
        round3_previous_detections = inter_rator.get_all_agreed_annotations()
        round3_annotated_ids = get_ids_in_subcategory(self.detections,round3_previous_detections)
        inter_rator = Round4DK41MarissaJulianResult()
        round4_previous_detections = inter_rator.get_all_agreed_annotations()
        round4_annotated_ids = get_ids_in_subcategory(self.detections,round4_previous_detections)
        beth_annotation = get_beth_positive_marking_for_DK41()
        beth_annotated_ids = get_ids_in_subcategory(self.detections,beth_annotation)
        all_annotated_ids = round3_annotated_ids+round4_annotated_ids+beth_annotated_ids
        self.detections = self.detections[[i not in all_annotated_ids for i in range(len(self.detections))]]

