import argparse
import os
import sys
import SimpleITK as sitk
from pathlib import Path
PIPELINE_ROOT = Path('./src/pipeline').absolute()
sys.path.append(PIPELINE_ROOT.as_posix())

from image_manipulation.filelocation_manager import FileLocationManager
from utilities.utilities_registration import create_rigid_parameters


def lines_that_start_with(string, fp):
    return [line for line in fp if line.startswith(string)]

def getMetricValue(logpath):
    with open(logpath, "r") as fp:
        for line in lines_that_start_with("Final", fp):
            return line

def align_elastix(animal, fixed_file, moving_file, moving_index):
    pixelType = sitk.sitkFloat32
    fixed = sitk.ReadImage(fixed_file, pixelType)
    moving = sitk.ReadImage(moving_file, pixelType)

    elastixImageFilter = sitk.ElastixImageFilter()
    elastixImageFilter.SetFixedImage(fixed)
    elastixImageFilter.SetMovingImage(moving)
    rigid_params = create_rigid_parameters(elastixImageFilter)
    # We reset this value below to a lower number as just want a metric
    # we can compare to other sections
    rigid_params["MaximumNumberOfIterations"] = ["80"]

    elastixImageFilter.SetParameterMap(rigid_params)
    # logging
    fileLocationManager = FileLocationManager(animal)
    OUTPUT = fileLocationManager.elastix
    elastixImageFilter.LogToConsoleOff();
    elastixImageFilter.LogToFileOn();
    logfile = str(moving_index).zfill(3) + ".tif"
    os.makedirs(OUTPUT, exist_ok=True)
    elastixImageFilter.SetOutputDirectory(OUTPUT);
    elastixImageFilter.SetLogFileName(logfile);    
    elastixImageFilter.Execute()
    logfilepath = os.path.join(OUTPUT, logfile)
    metric_value = getMetricValue(logfilepath)
    print(metric_value)

def create_image(fixed_file, moving_file, outfile):
    elastixImageFilter = sitk.ElastixImageFilter()
    pixelType = sitk.sitkFloat32
    fixed = sitk.ReadImage(fixed_file, pixelType)
    moving = sitk.ReadImage(moving_file, pixelType)
    elastixImageFilter.SetFixedImage(fixed)
    elastixImageFilter.SetMovingImage(moving)
    rigid_params = create_rigid_parameters(elastixImageFilter)
    # We reset this value below to a lower number as just want a metric
    # we can compare to other sections
    rigid_params["MaximumNumberOfIterations"] = ["2000"]

    elastixImageFilter.SetParameterMap(rigid_params)
    elastixImageFilter.LogToConsoleOff();
    elastixImageFilter.Execute()
    rigidTransform = elastixImageFilter.GetTransformParameterMap()[0]

    transformixFilter = sitk.TransformixImageFilter()
    transformixFilter.SetTransformParameterMap(rigidTransform)
    transformixFilter.SetMovingImage(moving)
    transformixFilter.Execute()
    transformed = transformixFilter.GetResultImage()
    transformed = sitk.Cast(transformed, sitk.sitkUInt16)
    print(f'Writing {outfile}')
    sitk.WriteImage(transformed, outfile)

def create_alignment(animal):
    fileLocationManager = FileLocationManager(animal)
    MOVING_DIR = os.path.join(fileLocationManager.prep, 'CH3', 'thumbnail_aligned_iteration_1')
    FIXED_DIR = fileLocationManager.get_thumbnail_aligned(channel=1)
    OUTPUT = fileLocationManager.get_thumbnail_aligned(channel=3) 
    moving_files = sorted(os.listdir(MOVING_DIR))

    for file in moving_files:
        moving_file = os.path.join(MOVING_DIR, file)
        fixed_file = os.path.join(FIXED_DIR, file)
        outfile = os.path.join(OUTPUT, file)
        create_image(fixed_file, moving_file, outfile)





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Work on Animal')
    parser.add_argument('--animal', help='Enter the animal', required=True)
    args = parser.parse_args()
    animal = args.animal
    
    create_alignment(animal)

