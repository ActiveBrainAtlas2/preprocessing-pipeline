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

# set base root of common files
CSHL_DIR = '/net/birdstore/Active_Atlas_Data/data_root/CSHL_volumes'

def check_exists_download(source, destination):
    if os.path.exists(destination) and len(os.listdir(destination)) > 0:
        print('Destination {} already exists and contains files',format(destination))
    else:
        os.makedirs(destination)
        command = ["aws", "s3", "cp", '--recursive', '--no-sign-request', source, destination]
        subprocess.call(command)




# Download operation config files
S3_OPERATION_CONFIGS = 's3://mousebrainatlas-data/operation_configs/'
LOCAL_OPERATION_CONFIGS = os.path.join(CSHL_DIR, 'all_brains')
check_exists_download(S3_OPERATION_CONFIGS, LOCAL_OPERATION_CONFIGS)

# Download mxnet files
S3_MXMODELS = 's3://mousebrainatlas-data/mxnet_models/inception-bn-blue/'
LOCAL_MXMODELS = os.path.join(CSHL_DIR, 'all_brains', 'mxnet_models', 'inception-bn-blue/')
check_exists_download(S3_MXMODELS, LOCAL_MXMODELS)

# Download AtlasV7 volume files
S3_ATLAS_VOLUMES = 's3://mousebrainatlas-data/CSHL_volumes/atlasV7/atlasV7_10.0um_scoreVolume/score_volumes/'
LOCAL_ATLAS_VOLUMES = os.path.join(CSHL_DIR, 'all_brains', 'atlasV7', 'atlasV7_10.0um_scoreVolume', 'score_volumes/')
check_exists_download(S3_ATLAS_VOLUMES, LOCAL_ATLAS_VOLUMES)

# Download all classifiers according to the list of detectors by detector ID
for id_detector in id_detectors:
    id_classifier = detector_settings.loc[id_detector]['feature_classifier_id']
    # s3_fp = 's3://mousebrainatlas-data/CSHL_classifiers/setting_'+str(id_classifier)+'/classifiers/'
    S3_FILES = 's3://mousebrainatlas-data/CSHL_classifiers/setting_{}/classifiers/'.format(str(id_classifier))
    LOCAL_FILES = os.path.join(ROOT_DIR, stack, 'brains_info', 'classifiers', 'setting_{}'.format(id_classifier),
                            'classifiers/')
    check_exists_download(S3_FILES, LOCAL_FILES)
