import sys
sys.path.append('/home/zhw272/programming/pipeline_utility')
from notebooks.Will.rough_alignment_demons import get_rough_alignment_demons_transform
braini = 'DK39'
transformi = get_rough_alignment_demons_transform(fixed_brain = braini)