import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.toolbox.brain_lists import get_prep_list_for_rough_alignment_test
from notebooks.Will.toolbox.IOs.get_landmark_lists import get_shared_landmarks_between_specimens
prep_list= get_prep_list_for_rough_alignment_test()
common_str = get_shared_landmarks_between_specimens(prep_list)