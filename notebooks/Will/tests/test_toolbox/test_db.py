import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from utilities.brain_specimens.get_prep_list import get_prep_list_excluding_DK52
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_shared_landmarks_between_specimens
prep_list_excluding_DK52 = get_prep_list_excluding_DK52()
common_landmarks = get_shared_landmarks_between_specimens(prep_list_excluding_DK52+['DK52'])