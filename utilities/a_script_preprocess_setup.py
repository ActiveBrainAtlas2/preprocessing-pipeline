import os
import argparse
import subprocess

from metadata import detector_settings, ROOT_DIR

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Downloads all relevant files from S3.')

parser.add_argument("stack", type=str, help="The name of the stack")
parser.add_argument("stain", type=str, help="Either \'NTB\' or \'Thionin\'.")
args = parser.parse_args()
stack = args.stack
stain = args.stain

if stain == "unknown":
    id_detectors = [799, 19]
elif stain.lower() == "ntb":
    id_detectors = [799]
elif stain.lower() == "thionin":
    id_detectors = [19]
else:
    id_detectors = [799, 19]


def create_folder_if_nonexistant(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Download operation config files
s3_fp = 's3://mousebrainatlas-data/operation_configs/'
local_fp = os.path.join( ROOT_DIR, stack, 'brains_info' )
create_folder_if_nonexistant( local_fp )
command = ["aws", "s3", "cp", '--recursive', '--no-sign-request',s3_fp, local_fp]
subprocess.call( command )
     
# Download mxnet files
s3_fp = 's3://mousebrainatlas-data/mxnet_models/inception-bn-blue/'
local_fp = os.path.join( ROOT_DIR, stack, 'brains_info', 'mxnet_models', 'inception-bn-blue/')
create_folder_if_nonexistant( local_fp )
command = ["aws", "s3", "cp", '--recursive', '--no-sign-request', s3_fp, local_fp]
subprocess.call( command )
    
# Download AtlasV7 volume files
s3_fp = 's3://mousebrainatlas-data/CSHL_volumes/atlasV7/atlasV7_10.0um_scoreVolume/score_volumes/'
local_fp = os.path.join( ROOT_DIR, stack, 'brains_info', 'CSHL_volumes', 'atlasV7', 'atlasV7_10.0um_scoreVolume', 'score_volumes/')
create_folder_if_nonexistant( local_fp )
command = ["aws", "s3", "cp", '--recursive', '--no-sign-request', s3_fp, local_fp]
subprocess.call( command )

# Download all classifiers according to the list of detectors
for id_detector in id_detectors:
    # Get the classifier ID from the detector ID
    id_classifier = detector_settings.loc[id_detector]['feature_classifier_id']

    # Download pre-trained classifiers for a particular setting
    s3_fp = 's3://mousebrainatlas-data/CSHL_classifiers/setting_'+str(id_classifier)+'/classifiers/'
    local_fp = os.path.join( ROOT_DIR, stack, 'brains_info', 'classifiers', 'setting_{}'.format(id_classifier), 'classifiers/')
    create_folder_if_nonexistant( local_fp )
    command = ["aws", "s3", "cp", '--recursive', '--no-sign-request', s3_fp, local_fp]
    subprocess.call( command )
