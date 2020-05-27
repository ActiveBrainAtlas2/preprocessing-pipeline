"""
was formerly warp_crop.py
"""
import argparse
import sys
import os
import subprocess
import numpy as np

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.file_location import FileLocationManager



parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""A versatile warp/crop script. 
Usage 1: warp_crop.py --input_spec in.ini --op_id align1crop1
This is the high-level usage. The operations are defined as ini files in the operation_configs/ folder.

Usage 2: warp_crop.py --input_fp in.tif --output_fp out.tif --op warp 0.99,0,0,0,1.1,0 --op crop 100,100,20,10
This is the low-level usage. Note that the user must ensure the warp parameters and crop coordinates are consistent with the resolution of the input image.
"""
)

#parser.add_argument("--stack", type=str)
parser.add_argument("--op", action='append', nargs=2)
parser.add_argument("--input_fp", type=str, help="input filepath")
parser.add_argument("--output_fp", type=str, help="output filepath")
parser.add_argument("--njobs", type=int, help="Number of parallel jobs", default=1)

args = parser.parse_args()

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import orientation_argparse_str_to_imagemagick_str, \
	convert_2d_transform_forms, convert_cropbox_fmt, create_parent_dir_if_not_exists

stack =  'DK39'
fileLocationManager = FileLocationManager(stack)
resolution = 'thumbnail'
tf_csv = os.path.join(fileLocationManager.brain_info, 'transforms_to_anchor.csv')
filepath = fileLocationManager.masked
image_name_list = sorted(os.listdir(filepath))

pad_color = 'black'
prep_id = None
version = 'NtbNormalized'
resol = 'thumbnail'
ops_in_prep_id = None
out_prep_id = 'alignedPadded'

print('args.op ', args.op)

op_str = ''
for op_type, op_params in args.op: # args.op is a list
	# revert the leading minus sign hack
	if op_params.startswith('^'):
		op_params = '-' + op_params[1:]

	sys.stdout.write("optype in alignemnt3a: {}\n".format(op_type))
	if op_type == 'warp':
		T = np.linalg.inv(convert_2d_transform_forms(transform=op_params, out_form=(3,3)))
		op_str += " +distort AffineProjection '%(sx)f,%(rx)f,%(ry)f,%(sy)f,%(tx)f,%(ty)f' " % {
					'sx':T[0,0], 'sy':T[1,1], 'rx':T[1,0], 'ry':T[0,1], 'tx':T[0,2], 'ty':T[1,2]}
		projections = "{}, {}, {}, {}, {}, {}".format(T[0,0], T[1,1], T[1,0], T[0,1], T[0,2], T[1,2])

	elif op_type == 'crop':
		x, y, w, h = convert_cropbox_fmt(data=op_params, out_fmt='arr_xywh', in_fmt='str_xywh', stack=stack)
		op_str += ' -crop %(w)sx%(h)s%(x)s%(y)s\! ' % {'x': '+' + str(x) if int(x) >= 0 else str(x),'y': '+' + str(y) if int(y) >= 0 else str(y),
													   'w': str(w),'h': str(h)}
		xa = str(x) if int(x) >= 0 else str(x)
		ya = str(y) if int(y) >= 0 else str(y)

		crops = "{}x{}+{}+{}!".format(xa, ya, w, h)

	elif op_type == 'rotate':
		op_str += ' ' + orientation_argparse_str_to_imagemagick_str[op_params]

	else:
		raise Exception("Op_id must be either warp or crop.")

assert args.input_fp is not None and args.output_fp is not None
input_fp = args.input_fp
output_fp = args.output_fp
create_parent_dir_if_not_exists(output_fp)
try:
	cmd = "convert %(input_fp)s  +repage -virtual-pixel background -background %(bg_color)s %(op_str)s -flatten -compress lzw \"%(output_fp)s\"" % \
			{'op_str': op_str, 'input_fp': input_fp, 'output_fp': output_fp, 'bg_color': pad_color}
	subprocess.call(cmd, shell=True)
	sys.stdout.write("IM: {}\n".format(cmd))
except Exception as e:
	sys.stderr.write("IM Error: {}\n".format(e))


