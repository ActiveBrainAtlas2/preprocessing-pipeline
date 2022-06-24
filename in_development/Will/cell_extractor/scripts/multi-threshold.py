from cell_extractor.CellDetector import CellDetector
from cell_extractor.DetectorMetrics import AnnotationProximityTool
import numpy as np
import pandas as pd
thresholds = [2000,2100,2200,2300,2700]
detections = []
scores = []
for threshold in thresholds:
    detector = CellDetector('DK55',round=2,segmentation_threshold=threshold)
    detection = detector.load_detections()
    sure = detection[detection.predictions == 2]
    unsure = detection[detection.predictions == 0]
    sure_score = pd.DataFrame({'mean':sure.mean_score,'std':sure.std_score})
    unsure_score = pd.DataFrame({'mean':unsure.mean_score,'std':unsure.std_score})
    sure = pd.DataFrame({'x':sure.col,'y':sure.row,'section':sure.section,'name':[f'{threshold}_sure' for _ in range(len(sure))]})
    unsure = pd.DataFrame({'x':unsure.col,'y':unsure.row,'section':unsure.section,'name':[f'{threshold}_unsure' for _ in range(len(unsure))]})
    detections.append(sure)
    detections.append(unsure)
    scores.append(sure_score)
    scores.append(unsure_score)
detections = pd.concat(detections)
scores = pd.concat(scores)
tool = AnnotationProximityTool()
tool.set_annotations_to_compare(detections)
tool.calculate_distance_matrix()
tool.find_close_pairs()
tool.group_and_label_close_pairs()
criteria = lambda pair_categories : tool.check(pair_categories,exclude=[f'{threshold}_unsure' for threshold in thresholds])

sure =[i for i in tool.pair_categories.values() if tool.check(i,exclude=[f'{threshold}_unsure' for threshold in thresholds])]
sure_pairs = [tool.pairs[id] for id,i in tool.pair_categories.items() if tool.check(i,exclude=[f'{threshold}_unsure' for threshold in thresholds])]
final_sure_detection = []
for id,_ in enumerate(sure):
    pair = sure_pairs[id]
    coords = tool.annotations_to_compare.iloc[pair]
    score = scores.iloc[pair]
    max_id = np.argmax(score.to_numpy()[:,0])
    final_sure_detection.append(coords.iloc[max_id])
final_sure_detection = pd.concat(final_sure_detection,axis=1).T
final_sure_detection.to_csv('/home/zhw272/DK55_combined_sure.csv')

def get_final_detection(thresholds,tool,scores,type='sure'):
    cell =[i for i in tool.pair_categories.values() if tool.check(i,exclude=[f'{threshold}_{type}' for threshold in thresholds])]
    cell_pairs = [tool.pairs[id] for id,i in tool.pair_categories.items() if tool.check(i,exclude=[f'{threshold}_{type}' for threshold in thresholds])]
    final_cell_detection = []
    for id,_ in enumerate(cell):
        pair = cell_pairs[id]
        coords = tool.annotations_to_compare.iloc[pair]
        score = scores.iloc[pair]
        max_id = np.argmax(score.to_numpy()[:,0])
        final_cell_detection.append(coords.iloc[max_id])
    final_cell_detection = pd.concat(final_cell_detection,axis=1).T
    return final_cell_detection

final_sure_detection = get_final_detection(thresholds,tool,scores,type = 'sure')
final_sure_detection.to_csv('/home/zhw272/DK55_combined_sure.csv')
final_unsure_detection = get_final_detection(thresholds,tool,scores,type = 'unsure')
final_unsure_detection.to_csv('/home/zhw272/DK55_combined_unsure.csv')
print()