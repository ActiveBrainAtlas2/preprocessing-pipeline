import os, sys
import numpy as np
import pandas as pd
import json
from skimage import io
import subprocess
#import tables
import configparser
#import bloscpack as bp
import pickle
import re
from six.moves import map

sys.path.append(os.path.join(os.getcwd(), '../'))

from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager


SCALING_FACTOR = 0.03125

def execute_command(cmd, stdout=None, stderr=None):
    retcode = subprocess.call(cmd, shell=True, stdout=stdout, stderr=stderr)
    sys.stderr.write('return code: %d\n' % retcode)


def run_distributed(stack, command, argument_type='single', kwargs_list=None, jobs_per_node=1, node_list=None, local_only=False, use_aws=False):
    run_distributed5(**locals())


def run_distributed5(stack, command, argument_type='single', kwargs_list=None, jobs_per_node=1, node_list=None,
                     local_only=False, use_aws=False):
    """
    Distributed executing a command.

    Args:
        local_only: run on local computer instead of AWS cluster
        jobs_per_node:
        kwargs_list: either dict of lists {kA: [vA1, vA2, ...], kB: [vB1, vB2, ...]} or list of dicts [{kA:vA1, kB:vB1}, {kA:vA2, kB:vB2}, ...].
        argument_type: one of list, list2, single. If command takes one input item as argument, use "single". If command takes a list of input items as argument, use "list2". If command takes an argument called "kwargs_str", use "list".
    """
    fileLocationManager = FileLocationManager(stack)

    if local_only:
        n_hosts = 1
    else:
        # Use a fixed node list rather than letting SGE automatically determine the node list.
        # This allows for control over which input items go to which node.
        if node_list is None:
            node_list = get_node_list()

        n_hosts = len(node_list)
        sys.stderr.write('%d nodes available.\n' % (n_hosts))
        if n_hosts == 0:
            print('NODE LIST LENGTH IS 0. NO HOSTS AVAILABLE')
            return

    if kwargs_list is None:
        kwargs_list = {'dummy': [None] * n_hosts}

    if isinstance(kwargs_list, dict):
        keys, vals = zip(*kwargs_list.items())
        kwargs_list_as_list = [dict(zip(keys, t)) for t in zip(*vals)]
        kwargs_list_as_dict = kwargs_list
    else:
        kwargs_list_as_list = kwargs_list
        keys = kwargs_list[0].keys()
        vals = [t.values() for t in kwargs_list]
        kwargs_list_as_dict = dict(zip(keys, zip(*vals)))

    assert argument_type in ['single', 'list', 'list2'], 'argument_type must be one of single, list, list2.'

    create_if_not_exists(fileLocationManager.mouseatlas_tmp)
    for node_i, (fi, li) in enumerate(first_last_tuples_distribute_over(0, len(kwargs_list_as_list) - 1, n_hosts)):

        temp_script = os.path.join(fileLocationManager.mouseatlas_tmp, 'runall.sh')
        temp_f = open(temp_script, 'w')
        for j, (fj, lj) in enumerate(first_last_tuples_distribute_over(fi, li, jobs_per_node)):
            if argument_type == 'list':
                line = command % {'kwargs_str': json.dumps(kwargs_list_as_list[fj:lj + 1])}
            elif argument_type == 'list2':
                line = command % {key: json.dumps(vals[fj:lj + 1]) for key, vals in kwargs_list_as_dict.items()}
            elif argument_type == 'single':
                # It is important to wrap command_templates and kwargs_list_str in apostrphes.
                # That lets bash treat them as single strings.
                # Reference: http://stackoverflow.com/questions/15783701/which-characters-need-to-be-escaped-in-bash-how-do-we-know-it
                lineXXX = "%(generic_launcher_path)s %(command_template)s %(kwargs_list_str)s" % \
                       {'generic_launcher_path': os.path.join(os.getcwd(), 'sequential_dispatcher.py'),
                        'command_template': command,
                        'kwargs_list_str': json.dumps(kwargs_list_as_list[fj:lj + 1])
                        }
                script = os.path.join(os.getcwd(), 'sequential_dispatcher.py')
                arguments = json.dumps(kwargs_list_as_list[fj:lj + 1])
                line = "{} '{}' '{}'\n".format(script, command, arguments)

            #temp_f.write(line + ' &\n')
            temp_f.write('{} \n'.format(line))

        #temp_f.write('wait')
        temp_f.close()
        os.chmod(temp_script, 0o770)

        # Explicitly specify the node to submit jobs.
        # By doing so, we can control which files are available in the local scratch space of which node.
        # One can then assign downstream programs to specific nodes so they can read corresponding files from local scratch.

        if use_aws:
            stdout_template = '/home/ubuntu/stdout_%d.log'
            stderr_template = '/home/ubuntu/stderr_%d.log'
        else:
            stdout_template = os.path.join(fileLocationManager.mouseatlas_tmp, 'stdout_%d.log')
            stderr_template = os.path.join(fileLocationManager.mouseatlas_tmp, 'stderr_%d.log')

        if local_only:
            stdout_f = open(stdout_template % node_i, "w")
            stderr_f = open(stderr_template % node_i, "w")
            subprocess.call(temp_script, shell=True, stdout=stdout_f, stderr=stderr_f)
        else:
            print('qsub -V -q all.q@%(node)s -o %(stdout_log)s -e %(stderr_log)s %(script)s' % \
            dict(node=node_list[node_i], script=temp_script, stdout_log=stdout_template % node_i,
                 stderr_log=stderr_template % node_i))

            subprocess.call('qsub -V -q all.q@%(node)s -o %(stdout_log)s -e %(stderr_log)s %(script)s' % \
                 dict(node=node_list[node_i], script=temp_script,
                      stdout_log=stdout_template % node_i, stderr_log=stderr_template % node_i),
                 shell=True)

    sys.stderr.write('Jobs submitted.\n')


def first_last_tuples_distribute_over(first_sec, last_sec, n_host):
    secs_per_job = (last_sec - first_sec + 1)/float(n_host)
    if secs_per_job < 1:
        first_last_tuples = [(i,i) for i in range(first_sec, last_sec+1)]
    else:
        first_last_tuples = [(int(first_sec+i*secs_per_job), int(first_sec+(i+1)*secs_per_job-1) if i != n_host - 1 else last_sec) for i in range(n_host)]
    return first_last_tuples


def get_node_list():
    s = subprocess.check_output("qhost | awk 'NR >= 4 { print $1 }'", shell=True).strip()
    print("qhost | awk 'NR >= 4 { print $1 }'")
    print(subprocess.check_output("qhosst | awk 'NR >= 4 { print $1 }'", shell=True))
    print(s)
    if len(s) == 0:
        return []
    else:
        return sorted(s.split('\n'))


def shell_escape(s):
    """
    Escape a string (treat it as a single complete string) in shell commands.
    """
    from tempfile import mkstemp
    fd, path = mkstemp()
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(s)
        cmd = r"""cat %s | sed -e "s/'/'\\\\''/g; 1s/^/'/; \$s/\$/'/" """ % path
        escaped_str = subprocess.check_output(cmd, shell=True)
    finally:
        os.remove(path)

    return escaped_str

def create_parent_dir_if_not_exists(fp):
    create_if_not_exists(os.path.dirname(fp))


def create_if_not_exists(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            sys.stderr.write('%s\n' % e)
    return path

def load_transforms(stack, downsample_factor=None, resolution=None, use_inverse=True, anchor_fn=None):
    """
    Args:
        use_inverse (bool): If True, load the 2-d rigid transforms that when multiplied
                            to a point on original space converts it to on aligned space.
                            In preprocessing, set to False, which means simply parse the transform files as they are.
        downsample_factor (float): the downsample factor of images that the output transform will be applied to.
        resolution (str): resolution of the image that the output transform will be applied to.
    """
    # set the animal info

    sqlController = SqlController(stack)
    planar_resolution = sqlController.scan_run.resolution
    string_to_voxel_size = sqlController.convert_resolution_string_to_um(stack, resolution)

    if resolution is None:
        assert downsample_factor is not None
        resolution = 'down%d' % downsample_factor

    fp = get_transforms_filename(stack, anchor_fn=anchor_fn)
    # download_from_s3(fp, local_root=THUMBNAIL_DATA_ROOTDIR)
    Ts_down32 = load_data(fp)
    if isinstance(Ts_down32.values()[0], list): # csv, the returned result are dict of lists
        Ts_down32 = {k: np.reshape(v, (3,3)) for k, v in Ts_down32.items()}

    if use_inverse:
        Ts_inv_rescaled = {}
        for fn, T_down32 in sorted(Ts_down32.items()):
            T_rescaled = T_down32.copy()
            T_rescaled[:2, 2] = T_down32[:2, 2] * 32. * planar_resolution / string_to_voxel_size
            T_rescaled_inv = np.linalg.inv(T_rescaled)
            Ts_inv_rescaled[fn] = T_rescaled_inv
        return Ts_inv_rescaled
    else:
        Ts_rescaled = {}
        for fn, T_down32 in sorted(Ts_down32.items()):
            T_rescaled = T_down32.copy()
            T_rescaled[:2, 2] = T_down32[:2, 2] * 32. * planar_resolution / string_to_voxel_size
            Ts_rescaled[fn] = T_rescaled

        return Ts_rescaled


def get_transforms_filename(stack, anchor_fn=None):
    fileLocationManager = FileLocationManager(stack)
    fp = os.path.join(fileLocationManager.brain_info, 'transforms_to_anchor.csv')
    return fp

def load_data(filepath, filetype=None):

    if not os.path.exists(filepath):
        sys.stderr.write('File does not exist: %s\n' % filepath)

    if filetype == 'bp':
        return bp.unpack_ndarray_file(filepath)
    elif filetype == 'npy':
        return np.load(filepath)
    elif filetype == 'image':
        return io.imread(filepath)
    elif filetype == 'hdf':
        try:
            return load_hdf(filepath)
        except:
            return load_hdf_v2(filepath)
    elif filetype == 'bbox':
        return np.loadtxt(filepath).astype(np.int)
    elif filetype == 'annotation_hdf':
        contour_df = pd.read_hdf(filepath, 'contours')
        return contour_df
    elif filetype == 'pickle':
        return pickle.load(open(filepath, 'r'))
    elif filetype == 'file_section_map':
        with open(filepath, 'r') as f:
            fn_idx_tuples = [line.strip().split() for line in f.readlines()]
            filename_to_section = {fn: int(idx) for fn, idx in fn_idx_tuples}
            section_to_filename = {int(idx): fn for fn, idx in fn_idx_tuples}
        return filename_to_section, section_to_filename
    elif filetype == 'label_name_map':
        label_to_name = {}
        name_to_label = {}
        with open(filepath, 'r') as f:
            for line in f.readlines():
                name_s, label = line.split()
                label_to_name[int(label)] = name_s
                name_to_label[name_s] = int(label)
        return label_to_name, name_to_label
    elif filetype == 'anchor':
        with open(filepath, 'r') as f:
            anchor_fn = f.readline().strip()
        return anchor_fn
    elif filetype == 'transform_params':
        with open(filepath, 'r') as f:
            lines = f.readlines()

            global_params = one_liner_to_arr(lines[0], float)
            centroid_m = one_liner_to_arr(lines[1], float)
            xdim_m, ydim_m, zdim_m  = one_liner_to_arr(lines[2], int)
            centroid_f = one_liner_to_arr(lines[3], float)
            xdim_f, ydim_f, zdim_f  = one_liner_to_arr(lines[4], int)

        return global_params, centroid_m, centroid_f, xdim_m, ydim_m, zdim_m, xdim_f, ydim_f, zdim_f
    elif filepath.endswith('ini'):
        return load_ini(filepath)
    else:
        sys.stderr.write('File type %s not recognized.\n' % filetype)


def load_hdf(fn, key='data'):
    """
    Used by loading features.
    """
    """
    with tables.open_file(fn, mode="r") as f:
        data = f.get_node('/'+key).read()
    return data
    """

def load_hdf_v2(fn, key='data'):
    return pd.read_hdf(fn, key)


def one_liner_to_arr(line, func):
    #####UPGRADE 2 -> 3 return np.array(map(func, line.strip().split()))
    return np.array(list(map(func, line.strip().split())))


def load_ini(fp, split_newline=True, convert_none_str=True, section='DEFAULT'):
    """
    Value of string None will be converted to Python None.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(fp):
        raise Exception("ini file %s does not exist." % fp)
    config.read(fp)
    input_spec = dict(config.items(section))
    input_spec = {k: v.split('\n') if '\n' in v else v for k, v in input_spec.items()}
    for k, v in input_spec.items():
        if not isinstance(v, list):
            if '.' not in v and v.isdigit():
                input_spec[k] = int(v)
            elif v.replace('.','',1).isdigit():
                input_spec[k] = float(v)
        elif v == 'None':
            if convert_none_str:
                input_spec[k] = None
    assert len(input_spec) > 0, "Failed to read data from ini file."
    return input_spec

def load_consecutive_section_transform(stack, moving_fn, fixed_fn):
    """
    Load pairwise transform.

    Returns:
        (3,3)-array.
    """
    assert stack is not None
    fileLocationManager = FileLocationManager(stack)
    elastix_output_dir = fileLocationManager.elastix_dir
    param_fp = os.path.join(elastix_output_dir, moving_fn + '_to_' + fixed_fn, 'TransformParameters.0.txt')
    #sys.stderr.write('Load elastix-computed transform: %s\n' % param_fp)
    if not os.path.exists(param_fp):
        raise Exception('Transform file does not exist: %s to %s, %s' % (moving_fn, fixed_fn, param_fp))
    transformation_to_previous_sec = parse_elastix_parameter_file(param_fp)

    return transformation_to_previous_sec


def parse_elastix_parameter_file(filepath, tf_type=None):
    """
    Parse elastix parameter result file.
    """

    d = parameter_elastix_parameter_file_to_dict(filepath)

    if tf_type is None:
        # For alignment composition script
        rot_rad, x_mm, y_mm = d['TransformParameters']
        center = np.array(d['CenterOfRotationPoint']) / np.array(d['Spacing'])
        # center[1] = d['Size'][1] - center[1]

        xshift = x_mm / d['Spacing'][0]
        yshift = y_mm / d['Spacing'][1]

        R = np.array([[np.cos(rot_rad), -np.sin(rot_rad)],
                      [np.sin(rot_rad), np.cos(rot_rad)]])
        shift = center + (xshift, yshift) - np.dot(R, center)
        T = np.vstack([np.column_stack([R, shift]), [0, 0, 1]])
        return T

    elif tf_type == 'rigid3d':
        p = np.array(d['TransformParameters'])
        center = np.array(d['CenterOfRotationPoint']) / np.array(d['Spacing'])
        shift = p[3:] / np.array(d['Spacing'])

        thetax, thetay, thetaz = p[:3]
        # Important to use the negative angle.
        cx = np.cos(-thetax)
        cy = np.cos(-thetay)
        cz = np.cos(-thetaz)
        sx = np.sin(-thetax)
        sy = np.sin(-thetay)
        sz = np.sin(-thetaz)
        Rx = np.array([[1, 0, 0], [0, cx, sx], [0, -sx, cx]])
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        Rz = np.array([[cz, sz, 0], [-sz, cz, 0], [0, 0, 1]])

        R = np.dot(np.dot(Rz, Ry), Rx)
        # R = np.dot(np.dot(Rx, Ry), Rz)
        # The order could be Rx,Ry,Rz - not sure.

        return R, shift, center

    elif tf_type == 'affine3d':
        p = np.array(d['TransformParameters'])
        L = p[:9].reshape((3, 3))
        shift = p[9:] / np.array(d['Spacing'])
        center = np.array(d['CenterOfRotationPoint']) / np.array(d['Spacing'])
        # shift = center + shift - np.dot(L, center)
        # T = np.column_stack([L, shift])
        return L, shift, center

    elif tf_type == 'bspline3d':
        n_params = d['NumberOfParameters']
        p = np.array(d['TransformParameters'])
        grid_size = d['GridSize']
        grid_spacing = d['GridSpacing']
        grid_origin = d['GridOrigin']

        return L, shift, center

def parameter_elastix_parameter_file_to_dict(filename):
    d = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            if line.startswith('('):
                tokens = line[1:-2].split(' ')
                key = tokens[0]
                if len(tokens) > 2:
                    value = []
                    for v in tokens[1:]:
                        try:
                            value.append(float(v))
                        except ValueError:
                            value.append(v)
                else:
                    v = tokens[1]
                    try:
                        value = (float(v))
                    except ValueError:
                        value = v
                d[key] = value
        return d


def create_warp_transforms(animal, transforms, transforms_resol, resolution):
    def convert_2d_transform_forms(arr):
        return np.vstack([arr, [0, 0, 1]])

    # transforms_resol = op['resolution']
    transforms_scale_factor = convert_resolution_string_to_um(animal,
                                                              resolution=transforms_resol) / convert_resolution_string_to_um(
        animal, resolution=resolution)
    tf_mat_mult_factor = np.array([[1, 1, transforms_scale_factor], [1, 1, transforms_scale_factor]])
    transforms_to_anchor = {
        img_name:
            convert_2d_transform_forms(np.reshape(tf, (3, 3))[:2] * tf_mat_mult_factor) for
        img_name, tf in transforms.items()}

    return transforms_to_anchor

def transform_create_alignment(points, transform):
    a = np.hstack((points, np.ones((points.shape[0], 1))))
    b = transform.T[:, 0:2]
    c = np.matmul(a, b)
    return c


def dict_to_csv(d, fp):
    df = pd.DataFrame.from_dict({k: np.array(v).flatten() for k, v in d.items()}, orient='index')
    df.to_csv(fp, header=False)


def csv_to_dict(fp):
    """
    First column contains keys.
    """
    df = pd.read_csv(fp, index_col=0, header=None)
    d = df.to_dict(orient='index')
    d = {k: v.values() for k, v in d.items()}
    return d


def convert_2d_transform_forms(transform, out_form):

    if isinstance(transform, str):
        if out_form == (2,3):
            #return np.reshape(map(np.float, transform.split(',')), (2,3))
            return np.reshape(list(map(np.float, transform.split(','))), (2, 3))
        elif out_form == (3,3):
            #return np.vstack([np.reshape(map(np.float, transform.split(',')), (2,3)), [0,0,1]])
            return np.vstack([np.reshape(list(map(np.float, transform.split(','))), (2, 3)), [0, 0, 1]])
    else:
        transform = np.array(transform)
        if transform.shape == (2,3):
            if out_form == (3,3):
                transform = np.vstack([transform, [0,0,1]])
            elif out_form == 'str':
                transform = ','.join(map(str, transform[:2].flatten()))
        elif transform.shape == (3,3):
            if out_form == (2,3):
                transform = transform[:2]
            elif out_form == 'str':
                transform = ','.join(map(str, transform[:2].flatten()))

    return transform


##### cropbox methods

def convert_cropbox_from_arr_xywh_1um(data, out_fmt, out_resol, stack):
    sqlController = SqlController(stack)
    string_to_um_out_resolution = sqlController.convert_resolution_string_to_um(stack, out_resol)

    data = data / string_to_um_out_resolution
    if out_fmt == 'str_xywh':
        return ','.join(map(str, data))
    elif out_fmt == 'dict':
        raise Exception("too lazy to implement")
    elif out_fmt == 'arr_xywh':
        return data
    elif out_fmt == 'arr_xxyy':
        return np.array([data[0], data[0]+data[2]-1, data[1], data[1]+data[3]-1])
    else:
        raise

def convert_cropbox_to_arr_xywh_1um(data, in_fmt, in_resol, stack):
    #print('data', data, 'in_fmt', in_fmt)
    sqlController = SqlController(stack)
    if isinstance(data, dict):
        data['rostral_limit'] = float(data['rostral_limit'])
        data['caudal_limit'] = float(data['caudal_limit'])
        data['dorsal_limit'] = float(data['dorsal_limit'])
        data['ventral_limit'] = float(data['ventral_limit'])
        arr_xywh = np.array([data['rostral_limit'], data['dorsal_limit'], data['caudal_limit'] - data['rostral_limit'] + 1, data['ventral_limit'] - data['dorsal_limit'] + 1])
        # Since this does not check for wrt, the user needs to make sure the cropbox is relative to the input prep (i.e. the wrt attribute is the same as input prep)
    elif isinstance(data, str):
        if in_fmt == 'str_xywh':
            d = re.sub('[!@#$cropwarp\]\[\']', '', data)
            l = d.split(',')
            a = [float(v) for v in l]
            arr_xywh = np.array(a)
        elif in_fmt == 'str_xxyy':
            #####UPGRADE from 2 to 3arr_xxyy = np.array(map(np.round, map(eval, data.split(','))))
            arr_xxyy = np.array(list(map(np.round, list(map(eval, data.split(','))))))
            arr_xywh = np.array([arr_xxyy[0], arr_xxyy[2], arr_xxyy[1] - arr_xxyy[0] + 1, arr_xxyy[3] - arr_xxyy[2] + 1])
        else:
            raise
    else:
        if in_fmt == 'arr_xywh':
            arr_xywh = data
            #arr_xywh = np.array(data)
        elif in_fmt == 'arr_xxyy':
            arr_xywh = np.array([data[0], data[2], data[1] - data[0] + 1, data[3] - data[2] + 1])
        else:
            print(in_fmt, data)
            raise

    string_to_um_in_resolution = sqlController.convert_resolution_string_to_um(stack, in_resol)
    arr_xywh_1um = arr_xywh * string_to_um_in_resolution
    print('arr_xywh_1um', arr_xywh_1um)
    return arr_xywh_1um


def convert_cropbox_fmt(out_fmt, data, in_fmt=None, in_resol='1um', out_resol='1um', stack=None):
    if in_resol == out_resol: # in this case, stack is not required/ Arbitrarily set both to 1um
        in_resol = '1um'
        out_resol = '1um'
    arr_xywh_1um = convert_cropbox_to_arr_xywh_1um(data=data, in_fmt=in_fmt, in_resol=in_resol, stack=stack)
    data_out = convert_cropbox_from_arr_xywh_1um(data=arr_xywh_1um, out_fmt=out_fmt, out_resol=out_resol, stack=stack)
    print('data out', data_out)
    return data_out


orientation_argparse_str_to_imagemagick_str =     {'transpose': '-transpose',
     'transverse': '-transverse',
     'rotate90': '-rotate 90',
     'rotate180': '-rotate 180',
     'rotate270': '-rotate 270',
     'rotate45': '-rotate 45',
     'rotate135': '-rotate 135',
     'rotate225': '-rotate 225',
     'rotate315': '-rotate 315',
     'flip': '-flip',
     'flop': '-flop'
    }


def convert_resolution_string_to_um(stack, resolution):
    return convert_resolution_string_to_voxel_size(stack, resolution)

def convert_resolution_string_to_voxel_size(stack, resolution):
    """
    Args:
        resolution (str):
    Returns:
        voxel/pixel size in microns.
    """
    try:
        sqlController = SqlController(stack)
        planar_resolution = sqlController.scan_run.resolution
    except:
        planar_resolution = 0.452
    #planar_resolution =  0.452
    assert resolution is not None, 'Resolution argument cannot be None.'

    if resolution in ['down32', 'thumbnail']:
        assert stack is not None
        return planar_resolution * 32.
    elif resolution == 'lossless' or resolution == 'down1' or resolution == 'raw' or resolution == 'full':
        assert stack is not None
        return planar_resolution
    elif resolution.startswith('down'):
        assert stack is not None
        return planar_resolution * int(resolution[4:])
    elif resolution == 'um':
        return 1.
    elif resolution.endswith('um'):
        return float(resolution[:-2])
    else:
        print(resolution)
        raise Exception("Unknown resolution string %s" % resolution)


def convert_2d_transform_forms(transform, out_form):
    print('convert_2d_transform_forms', type(transform), transform.shape, out_form)
    if isinstance(transform, str):
        if out_form == (2,3):
            return np.reshape(map(np.float, transform.split(',')), (2,3))
        elif out_form == (3,3):
            return np.vstack([np.reshape(map(np.float, transform.split(',')), (2,3)), [0,0,1]])
    else:
        #transform = np.array(transform)
        if transform.shape == (2,3):
            if out_form == (3,3):
                transform = np.vstack([transform, [0,0,1]])
            elif out_form == 'str':
                transform = ','.join(map(str, transform[:2].flatten()))
        elif transform.shape == (3,3):
            if out_form == (2,3):
                transform = transform[:2]
            elif out_form == 'str':
                transform = ','.join(map(str, transform[:2].flatten()))

    return transform


def get_last_2d(data):
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)


