"""
was formerly warp_crop.py
    If op is warp, return {image_name: (3,3)-array}.
    If op is crop, return {image_name: (x,y,w,h)}.
"""
import sys
import os
import argparse
import numpy as np
from collections import defaultdict
from itertools import chain

sys.path.append(os.path.join(os.getcwd(), '../'))
from utilities.alignment_utility import csv_to_dict, convert_2d_transform_forms, convert_cropbox_fmt, \
	load_ini, run_distributed
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController

def warp_image(op, resol, inverse=False, return_str=False, stack=None):
	sqlController = SqlController()
	fileLocationManager = FileLocationManager(stack)
	tf_csv = os.path.join(fileLocationManager.brain_info, 'transforms_to_anchor.csv')
	transforms_to_anchor = csv_to_dict(tf_csv)
	transforms_resol = op['resolution']
	string_to_um_from_resolution = sqlController.convert_resolution_string_to_um(stack, transforms_resol)
	string_to_um_to_resolution = sqlController.convert_resolution_string_to_um(stack, resol)

	# transforms_resol = op['resolution']
	transforms_scale_factor = string_to_um_from_resolution / string_to_um_to_resolution
	tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])

	if inverse:
		transforms_to_anchor = {
			img_name: convert_2d_transform_forms(np.linalg.inv(np.reshape(tf, (3, 3)))[:2] * tf_mat_mult_factor,
												 out_form='str') for img_name, tf in transforms_to_anchor.items()}
	else:
		transforms_to_anchor = {
			img_name: convert_2d_transform_forms(np.reshape(list(tf), (3, 3))[:2] * tf_mat_mult_factor, out_form='str') for
			img_name, tf in transforms_to_anchor.items()}

	return transforms_to_anchor

def crop_image(op, resol, inverse=False, return_str=False, stack=None):
	fileLocationManager = FileLocationManager(stack)
	fileLocationManager = FileLocationManager(stack)
	image_name_list = sorted(os.listdir(fileLocationManager.masked))
	cropbox_resol = op['resolution']

	if 'cropboxes_csv' in op:  # each image has a different cropbox
		cropbox_csv = os.path.join(fileLocationManager.brain_info, 'cropbox.csv')
		cropboxes_all = csv_to_dict(cropbox_csv)

		cropboxes = {}
		for img_name in image_name_list:
			arr_xxyy = convert_cropbox_fmt(data=cropboxes_all[img_name], in_fmt='arr_xywh', out_fmt='arr_xxyy')
			if inverse:
				arr_xxyy = np.array([-arr_xxyy[0], arr_xxyy[1], -arr_xxyy[2], arr_xxyy[3]])
			cropboxes[img_name] = convert_cropbox_fmt(data=arr_xxyy, in_fmt='arr_xxyy',
													  out_fmt='str_xywh' if return_str else 'arr_xywh',
													  in_resol=cropbox_resol, out_resol=resol, stack=stack)
	else:  # a single cropbox for all images
		arr_xxyy = convert_cropbox_fmt(data=op, in_fmt='dict', out_fmt='arr_xxyy', in_resol=cropbox_resol,
									   out_resol=resol, stack=stack)
		if inverse:
			arr_xxyy = np.array([-arr_xxyy[0], arr_xxyy[1], -arr_xxyy[2], arr_xxyy[3]])
		cropbox = convert_cropbox_fmt(data=arr_xxyy, in_fmt='arr_xxyy',
									  out_fmt='str_xywh' if return_str else 'arr_xywh', stack=stack)
		cropboxes = {img_name: cropbox for img_name in image_name_list}

	return cropboxes


def convert_operation_to_arr(op, resol, inverse=False, return_str=False, stack=None):
	if op['type'] == 'warp':
		transforms_to_anchor = warp_image(op, resol, inverse, return_str, stack)
		return transforms_to_anchor

	elif op['type'] == 'crop':
		cropboxes = crop_image(op, resol, inverse, return_str, stack)
		return cropboxes

	elif op['type'] == 'rotate':
		fileLocationManager = FileLocationManager(stack)
		image_name_list = sorted(os.listdir(fileLocationManager.masked))
		return {img_name: op['how'] for img_name in image_name_list}

	else:
		raise Exception("Operation type specified by ini must be either warp, crop or rotate.")


def parse_operation_sequence(op_name, resol, return_str=False, stack=None):
	fileLocationManager = FileLocationManager(stack)
	inverse = op_name.startswith('-')
	if inverse:
		op_name = op_name[1:]

	op_path = os.path.join(fileLocationManager.operation_configs,  '{}.ini'.format(op_name))
	op = load_ini(op_path)
	if op is None:
		raise Exception("Cannot load %s.ini" % op_name)

	if 'operation_sequence' in op: # composite operation
		assert not inverse, "Inverse composite operation is not implemented."
		op_seq = list(chain(*map(lambda o: parse_operation_sequence(o, resol=resol, return_str=return_str, stack=stack), op['operation_sequence'])))
		assert all([op_seq[i][3] == op_seq[i+1][2] for i in range(0, len(op_seq)-1)]), "In and out domains are not consistent along the composite operation chain. %s" % [(o[2], o[3]) for o in op_seq]

	else: # single operation
		op_arr = convert_operation_to_arr(op, resol=resol, inverse=inverse, return_str=return_str, stack=stack)
		if inverse:
			op_seq = [(op['type'], op_arr, op['dest_prep_id'], op['base_prep_id'])]
		else:
			op_seq = [(op['type'], op_arr, op['base_prep_id'], op['dest_prep_id'])]

	return op_seq

def setup(stack):
	"""
	This script calls itself. The first time, the argument: op_id = from_none_to_padded
	op_type initially equals warp
	Args:
		stack:

	Returns:
	"""
	fileLocationManager = FileLocationManager(stack)
	image_name_list = sorted(os.listdir(fileLocationManager.cleaned))
	resol = 'thumbnail'
	ops_in_prep_id = None
	out_prep_id = 'alignedPadded'
	op_id = 'from_none_to_padded'
	op_seq = parse_operation_sequence(op_id, resol=resol, return_str=True, stack=stack)

	ops_str_all_images = defaultdict(str)
	for op_type, op_params_str_all_images, _, _ in op_seq:
		for img_name, op_params_str in op_params_str_all_images.items():
			# replace leading minus sign with ^ to satisfy argparse
			if op_params_str.startswith('-'):
				op_params_str = '^' + op_params_str[1:]

			ops_str_all_images[img_name] += ' --op %s %s ' % (op_type, op_params_str)


	# sequantial_dispatcher argument cannot be too long, so we must limit the number of images processed each time
	batch_size = 100

	infilepath = fileLocationManager.cleaned
	outfilepath = fileLocationManager.aligned
	for batch_id in range(0, len(image_name_list), batch_size):

		script = os.path.join(os.getcwd(), 'alignment3a.py')
		ops = ops_str_all_images[img_name]
		input_fp = os.path.join(infilepath, img_name)
		output_fp = os.path.join(outfilepath, img_name)
		#cmd = 'python {} --input_fp {} --output_fp {} {}'.format(script, input_fp, output_fp)
		#run_distributed(stack, cmd, argument_type='single', jobs_per_node=4, local_only=True, kwargs_list="")
		"""
		run_distributed(stack, 'python %(script)s --input_fp \"%%(input_fp)s\" --output_fp \"%%(output_fp)s\" %%(ops_str)s' % \
		{'script':  script},
		kwargs_list=[{'ops_str': ops_str_all_images[img_name],
				'input_fp': os.path.join(infilepath, img_name),
				  'output_fp': os.path.join(outfilepath, img_name)}
				for img_name in image_name_list[batch_id:batch_id+batch_size]],
		argument_type='single', jobs_per_node=4, local_only=True)
		"""

		run_distributed(stack, 'python %(script)s --input_fp \"%%(input_fp)s\" --output_fp \"%%(output_fp)s\" %%(ops_str)s' % \
		{'script':  script},
		kwargs_list=[{'ops_str': ops_str_all_images[img_name],
				'input_fp': os.path.join(infilepath, img_name),
				'output_fp': os.path.join(outfilepath, img_name)}
				for img_name in image_name_list[batch_id:batch_id+batch_size]],
		argument_type='single', jobs_per_node=1, local_only=True)





if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Work on Animal')
	parser.add_argument('--animal', help='Enter the animal animal', required=True)
	args = parser.parse_args()
	animal = args.animal
	setup(animal)

