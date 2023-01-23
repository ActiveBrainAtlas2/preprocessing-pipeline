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
    rigid_params["MaximumNumberOfIterations"] = ["20"]

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


if __name__ == '__main__':
    animal = sys.argv[1]
    fixed = sys.argv[2]
    moving = sys.argv[3]
    moving_index = os.path.basename(moving)
    moving_index = str(moving_index).replace(".tif","")
    align_elastix(animal, fixed, moving, moving_index)

