import os
import sys

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.contour_utilities import image_contour_generator

stack = 'MD589'
detector_id = 19
structure = '12N'
str_contour, first_sec, last_sec = image_contour_generator(stack, detector_id, structure, use_local_alignment=True,
                                                           image_prep=2, threshold=0.2)
