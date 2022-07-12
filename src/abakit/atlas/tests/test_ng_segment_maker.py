from abakit.atlas.NgSegmentMaker import NgConverter
import numpy as np
import os
import shutil
import pytest
from util import get_test_volume_maker
from abakit.lib.python_util import read_file

def run_ng_segment_maker_on_test_volume(vmaker,output_dir):
    structure = 'test'
    maker = NgConverter(volume = vmaker.volumes[structure].astype(np.uint8),scales = [1,1,1],offset=list(vmaker.origins[structure]))
    segment_properties  = [('1','test')]
    maker.create_neuroglancer_files(output_dir,segment_properties)

def set_up():
    test_folder = os.path.dirname(__file__)
    output_dir = test_folder+'/ngsegment_test'
    vmaker = get_test_volume_maker()
    correct_info_file = read_file(test_folder+'/example_info_file')
    return output_dir,vmaker,correct_info_file

def check_the_currect_folders_and_files_are_created(output_dir,correct_info_file):
    assert os.path.exists(output_dir)
    assert np.all([i in ['info', '1_1_1', 'names', 'provenance', 'mesh_mip_0_err_40'] for i in os.listdir(output_dir)])
    assert os.path.getsize(output_dir) >50
    info_file = read_file(output_dir+'/info')
    assert info_file == correct_info_file

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_contour_to_segments():
    '''Tests the VolumeToContour class which turns a 3D mask to a set of contours. 
    The test create a mockup volume and checks if the correct contours are generated.'''
    output_dir,vmaker,correct_info_file = set_up()
    run_ng_segment_maker_on_test_volume(vmaker,output_dir)
    check_the_currect_folders_and_files_are_created(output_dir,correct_info_file)
    shutil.rmtree(output_dir)