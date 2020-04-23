import os
import argparse
#import SimpleITK as sitk
import  subprocess

from utilities.metadata import REPO_DIR, ELASTIX_BIN
from utilities.metadata import load_ini, UTILITY_DIR
from utilities.distributed_utilities import run_distributed
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""Align consecutive images. Possible bad alignment pairs are written into a separate file.
Usage 1: align.py in.ini --prep_id alignedPadded
Usage 2: align.py in.ini --elastix_output_dir DEMO998_elastix_output/ --param_fp params.txt
Usage 3: align.py in.ini --op from_none_to_aligned
"""
)

parser.add_argument("input_spec", type=str, help="input specifier. ini")
parser.add_argument("--op", type=str, help="operation id")
parser.add_argument("--prep_id", type=str, help="Prep id of the warp operation.")
parser.add_argument("--elastix_output_dir", type=str, help="output dir. Files for each pairwise transform are stored in sub-folder <currImageName>_to_<prevImageName>.")
parser.add_argument("--param_fp", type=str, help="elastix parameter file path")
#parser.add_argument("-r", help="re-generate even if already exists", action='store_true')

args = parser.parse_args()

input_spec = load_ini(args.input_spec)
stack = input_spec['stack']
sqlController = SqlController()
fileLocationManager = FileLocationManager(stack)

prep_id = input_spec['prep_id']
if prep_id == 'None':
    prep_id = None
resol = input_spec['resol']
version = input_spec['version']
if version == 'None':
    version = None
image_name_list = input_spec['image_name_list']
#if image_name_list == 'all':

    #image_name_list = map(lambda x: x[0], sorted(DataManager.load_sorted_filenames(stack=stack)[0].items(), key=lambda x: x[1]))
    #image_name_list = DataManager.load_sorted_filenames(stack=stack)[0].keys()

image_name_list = sqlController.get_image_list(stack, 'destination')

if args.op is not None:
    op = load_ini(os.path.join(fileLocationManager.operation_configs, args.op + '.ini'))
    assert op['type'] == 'warp', "Op must be a warp"
    assert op['base_prep_id'] == input_spec['prep_id'], "Op has base prep %s, but input has prep %s." % (op['base_prep_id'], input_spec['prep_id'])
else:
    assert args.param_fp is not None, "Must provide param_fp"
stop = len(image_name_list) - 1
params_fp = os.path.join(REPO_DIR, 'preprocess', 'parameters', 'Parameters_Rigid_MutualInfo_noNumberOfSpatialSamples_4000Iters.txt')
##### TODO, this is only working on the thumbnail dir for now
for i, file in enumerate(image_name_list):
    if i == stop:
        break
    print('len of images ', stop, i)
    fixed_image = os.path.join(fileLocationManager.thumbnail_prep, image_name_list[i])
    moving_image = os.path.join(fileLocationManager.thumbnail_prep, image_name_list[i+1])
    command = [ELASTIX_BIN, '-f', fixed_image, '-m', moving_image, '-p', params_fp, '-out', fileLocationManager.elastix_dir]
    #command = ['touch', os.path.join(fileLocationManager.elastix_dir, 'result.0.tif')]
    print(" ".join(command))
    ret = subprocess.run(command)
    os.rename(os.path.join(fileLocationManager.elastix_dir, 'result.0.tif'),
              os.path.join(fileLocationManager.elastix_dir, image_name_list[i]))
    print('command returned ', ret.returncode)

"""
ORIENTED = fileLocationManager.thumbnail_prep
ORIENTS = image_name_list
fixedFilename = os.path.join(ORIENTED, ORIENTS[0])
movingFilename = os.path.join(ORIENTED, ORIENTS[1])
fixedImage = sitk.ReadImage(fixedFilename)
movingImage = sitk.ReadImage(movingFilename)
parameterMap = sitk.GetDefaultParameterMap('translation')
# parameterMap = sitk.GetDefaultParameterMap("rigid")
# parameterMap["Transform"] = ["AffineTransform"]

elastixImageFilter = sitk.ElastixImageFilter()
elastixImageFilter.LogToConsoleOn()
elastixImageFilter.SetFixedImage(fixedImage)
elastixImageFilter.SetMovingImage(movingImage)
elastixImageFilter.SetParameterMap(parameterMap)
elastixImageFilter.Execute()

resultImage = elastixImageFilter.GetResultImage()
transformParameterMap = elastixImageFilter.GetTransformParameterMap()

transformixImageFilter = sitk.TransformixImageFilter()
transformixImageFilter.SetTransformParameterMap(transformParameterMap)
transformixImageFilter.


for filename in ORIENTS:
    input_file = os.path.join(ORIENTED, filename)
    transformixImageFilter.SetMovingImage(sitk.ReadImage(input_file))
    transformixImageFilter.Execute()
    filepath = os.path.join(fileLocationManager.elastix_dir, filename)
    img = transformixImageFilter.GetResultImage()
    sitk.WriteImage(transformixImageFilter.GetResultImage(), filepath)


run_distributed(stack, "python %(script)s \"%(output_dir)s\" \'%%(kwargs_str)s\' -p %(param_fp)s -r" % \
                {'script': os.path.join(UTILITY_DIR, 'align_sequential.py'),
                'output_dir': fileLocationManager.elastix_dir,
                 'param_fp': params_fp
                },
                kwargs_list=[{'prev_img_name': image_name_list[i-1],
                              'curr_img_name': image_name_list[i],
                              'prev_fp': os.path.join(fileLocationManager.oriented, image_name_list[i-1]),
                              'curr_fp': os.path.join(fileLocationManager.oriented, image_name_list[i])
                             }
                            for i in range(1, len(image_name_list))],
                argument_type='list',
                jobs_per_node=8,
               local_only=True)
"""
