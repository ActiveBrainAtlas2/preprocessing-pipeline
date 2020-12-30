import os
import subprocess

from utilities.metadata import detector_settings
from utilities.file_location import FileLocationManager




def check_exists_download(source, destination):
    if os.path.exists(destination) and len(os.listdir(destination)) > 0:
        print('Destination {} already exists and contains files'.format(destination))
    else:
        os.makedirs(destination)
        command = ["aws", "s3", "cp", '--recursive', '--no-sign-request', source, destination]
        subprocess.call(command)

def preprocess_setup(stack, stain):
    # set base root of common files
    fileLocationManager = FileLocationManager(stack)

    if stain == "unknown":
        id_detectors = [799, 19]
    elif stain.lower() == "ntb":
        id_detectors = [799]
    elif stain.lower() == "thionin":
        id_detectors = [19]
    else:
        id_detectors = [799, 19]


    # Download operation config files
    S3_OPERATION_CONFIGS = 's3://mousebrainatlas-data/operation_configs/'
    check_exists_download(S3_OPERATION_CONFIGS, fileLocationManager.operation_configs)

    # Download mxnet files
    S3_MXMODELS = 's3://mousebrainatlas-data/mxnet_models/inception-bn-blue/'
    LOCAL_MXMODELS = os.path.join(fileLocationManager.mxnet_models, 'inception-bn-blue/')
    check_exists_download(S3_MXMODELS, LOCAL_MXMODELS)

    # Download AtlasV7 volume files
    S3_ATLAS_VOLUMES = 's3://mousebrainatlas-data/CSHL_volumes/atlasV7/atlasV7_10.0um_scoreVolume/score_volumes/'
    check_exists_download(S3_ATLAS_VOLUMES, fileLocationManager.atlas_volume)

    # Download all classifiers according to the list of detectors by detector ID
    for id_detector in id_detectors:
        id_classifier = detector_settings.loc[id_detector]['feature_classifier_id']
        # s3_fp = 's3://mousebrainatlas-data/CSHL_classifiers/setting_'+str(id_classifier)+'/classifiers/'
        S3_FILES = 's3://mousebrainatlas-data/CSHL_classifiers/setting_{}/classifiers/'.format(str(id_classifier))
        LOCAL_FILES = os.path.join(fileLocationManager.classifiers, 'setting_{}'.format(id_classifier))
        check_exists_download(S3_FILES, LOCAL_FILES)
