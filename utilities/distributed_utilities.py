import json
import os
import sys
import subprocess

from utilities.metadata import (ENABLE_UPLOAD_S3, ENABLE_DOWNLOAD_S3,
                      HOST_ID,
                      S3_DATA_BUCKET, S3_RAWDATA_BUCKET, ROOT_DIR)

from utilities.metadata import DATA_ROOTDIR, UTILITY_DIR
from utilities.utilities2015 import create_if_not_exists, shell_escape, execute_command
from utilities.file_location import FileLocationManager

XXXdefault_root = dict(localhost='/home/yuncong',
                    # workstation='/media/yuncong/BstemAtlasData',
                    workstation='/data',
                    oasis='/home/yuncong/csd395', s3=S3_DATA_BUCKET, ec2='/shared', ec2scratch='/scratch',
                    s3raw=S3_RAWDATA_BUCKET)


def upload_to_s3(fp, local_root=None, is_dir=False):
    """
    Args:
        fp (str): file path
        local_root (str): default to ROOT_DIR
    """

    if not ENABLE_UPLOAD_S3:
        sys.stderr.write("ENABLE_UPLOAD_S3 is False. Skip uploading to S3.\n")
        return

    # Not using keyword default value because ROOT_DIR might be dynamically assigned rather than set at module importing.
    if local_root is None:
        if '/media/yuncong/YuncongPublic' in fp:
            local_root = '/media/yuncong/YuncongPublic'
        # elif '/media/yuncong/BstemAtlasData' in fp:
        elif fp.startswith('/data'):
            # local_root = '/media/yuncong/BstemAtlasData'
            local_root = '/data'
        else:
            local_root = ROOT_DIR

    transfer_data_synced(relative_to_local(fp, local_root=local_root),
                         from_hostname=HOST_ID,
                         to_hostname='s3',
                         is_dir=is_dir,
                         from_root=local_root)


def download_from_s3(fp, local_root=None, is_dir=False, redownload=False, include_only=None):
    """
    Args:
        fp (str): file path
        local_root (str): default to ROOT_DIR
    """

    if not ENABLE_DOWNLOAD_S3:
        sys.stderr.write("ENABLE_DOWNLOAD_S3 is False. Skip downloading from S3.\n")
        return

    # Not using keyword default value because ROOT_DIR might be dynamically assigned rather than set at module importing.
    if local_root is None:
        if '/media/yuncong/YuncongPublic' in fp:
            local_root = '/media/yuncong/YuncongPublic'
        # elif '/media/yuncong/BstemAtlasData' in fp:
        elif fp.startswith('/data'):
            # local_root = '/media/yuncong/BstemAtlasData'
            local_root = '/data'
        else:
            local_root = ROOT_DIR

    if redownload or not os.path.exists(fp):
        # TODO: even if the file exists, it might be incomplete. A more reliable way is to check if the sizes of two files match.
        transfer_data_synced(relative_to_local(fp, local_root=local_root),
                             from_hostname='s3',
                             to_hostname=HOST_ID,
                             is_dir=is_dir,
                             to_root=local_root,
                             include_only=include_only)


def transfer_data_synced(fp_relative, from_hostname, to_hostname, is_dir, from_root=None, to_root=None,
                         include_only=None, exclude_only=None, includes=None, s3_bucket=None):
    if from_root is None:
        from_root = default_root[from_hostname]
    if to_root is None:
        to_root = default_root[to_hostname]

    from_fp = os.path.join(from_root, fp_relative)
    to_fp = os.path.join(to_root, fp_relative)
    transfer_data(from_fp=from_fp, to_fp=to_fp, from_hostname=from_hostname, to_hostname=to_hostname, is_dir=is_dir,
                  include_only=include_only, exclude_only=exclude_only, includes=includes)


def relative_to_local(abs_fp, local_root=None):
    if local_root is None:
        local_root = ROOT_DIR
    # http://stackoverflow.com/questions/7287996/python-get-relative-path-from-comparing-two-absolute-paths
    common_prefix = os.path.commonprefix([abs_fp, local_root])
    relative_path = os.path.relpath(abs_fp, common_prefix)
    return relative_path


def transfer_data(from_fp, to_fp, from_hostname, to_hostname, is_dir, include_only=None, exclude_only=None,
                  includes=None):
    assert from_hostname in ['localhost', 'workstation', 'oasis', 's3', 'ec2', 's3raw',
                             'ec2scratch'], 'from_hostname must be one of localhost, workstation, oasis, s3, s3raw, ec2 or ec2scratch.'
    assert to_hostname in ['localhost', 'workstation', 'oasis', 's3', 'ec2', 's3raw',
                           'ec2scratch'], 'to_hostname must be one of localhost, workstation, oasis, s3, s3raw, ec2 or ec2scratch.'

    to_parent = os.path.dirname(to_fp)


    if from_hostname in ['localhost', 'ec2', 'workstation', 'ec2scratch']:
        # upload
        if to_hostname in ['s3', 's3raw']:
            if is_dir:
                if includes is not None:
                    execute_command(
                        'aws s3 cp --recursive \"%(from_fp)s\" \"s3://%(to_fp)s\" --exclude \"*\" %(includes_str)s' % dict(
                            from_fp=from_fp, to_fp=to_fp,
                            includes_str=" ".join(['--include ' + incl for incl in includes])))
                elif include_only is not None:
                    execute_command(
                        'aws s3 cp --recursive \"%(from_fp)s\" \"s3://%(to_fp)s\" --exclude \"*\" --include \"%(include)s\"' % dict(
                            from_fp=from_fp, to_fp=to_fp, include=include_only))
                elif exclude_only is not None:
                    execute_command(
                        'aws s3 cp --recursive \"%(from_fp)s\" \"s3://%(to_fp)s\" --include \"*\" --exclude \"%(exclude)s\"' % dict(
                            from_fp=from_fp, to_fp=to_fp, exclude=exclude_only))
                else:
                    execute_command('aws s3 cp --recursive \"%(from_fp)s\" \"s3://%(to_fp)s\"' % \
                                    dict(from_fp=from_fp, to_fp=to_fp))
            else:
                execute_command('aws s3 cp \"%(from_fp)s\" \"s3://%(to_fp)s\"' % \
                                dict(from_fp=from_fp, to_fp=to_fp))
        else:
            execute_command(
                "ssh %(to_hostname)s 'rm -rf \"%(to_fp)s\" && mkdir -p \"%(to_parent)s\"' && scp -r \"%(from_fp)s\" %(to_hostname)s:\"%(to_fp)s\"" % \
                dict(from_fp=from_fp, to_fp=to_fp, to_hostname=to_hostname, to_parent=to_parent))
    elif to_hostname in ['localhost', 'ec2', 'workstation', 'ec2scratch']:
        # download
        if from_hostname in ['s3', 's3raw']:

            # Clear existing folder/file
            if not include_only and not includes and not exclude_only:
                execute_command(
                    'rm -rf \"%(to_fp)s\" && mkdir -p \"%(to_parent)s\"' % dict(to_parent=to_parent, to_fp=to_fp))

            # Download from S3 using aws commandline interface.
            if is_dir:
                if includes is not None:
                    execute_command(
                        'aws s3 cp --recursive \"s3://%(from_fp)s\" \"%(to_fp)s\" --exclude \"*\" %(includes_str)s' % dict(
                            from_fp=from_fp, to_fp=to_fp,
                            includes_str=" ".join(['--include ' + incl for incl in includes])))
                elif include_only is not None:
                    execute_command(
                        'aws s3 cp --recursive \"s3://%(from_fp)s\" \"%(to_fp)s\" --exclude \"*\" --include \"%(include)s\"' % dict(
                            from_fp=from_fp, to_fp=to_fp, include=include_only))
                elif exclude_only is not None:
                    execute_command(
                        'aws s3 cp --recursive \"s3://%(from_fp)s\" \"%(to_fp)s\" --include \"*\" --exclude \"%(exclude)s\"' % dict(
                            from_fp=from_fp, to_fp=to_fp, exclude=exclude_only))
                else:
                    execute_command(
                        'aws s3 cp --recursive \"s3://%(from_fp)s\" \"%(to_fp)s\"' % dict(from_fp=from_fp, to_fp=to_fp))
            else:
                execute_command('aws s3 cp \"s3://%(from_fp)s\" \"%(to_fp)s\"' % dict(from_fp=from_fp, to_fp=to_fp))
        else:
            execute_command(
                "scp -r %(from_hostname)s:\"%(from_fp)s\" \"%(to_fp)s\"" % dict(from_fp=from_fp, to_fp=to_fp,
                                                                                from_hostname=from_hostname))
    else:
        # log onto another machine and perform upload from there.
        execute_command(
            "ssh %(from_hostname)s \"ssh %(to_hostname)s \'rm -rf \"%(to_fp)s\" && mkdir -p %(to_parent)s && scp -r \"%(from_fp)s\" %(to_hostname)s:\"%(to_fp)s\"\'\"" % \
            dict(from_fp=from_fp, to_fp=to_fp, from_hostname=from_hostname, to_hostname=to_hostname,
                 to_parent=to_parent))

def get_node_list():
    s = subprocess.check_output("qhost | awk 'NR >= 4 { print $1 }'", shell=True).strip()
    print("qhost | awk 'NR >= 4 { print $1 }'")
    print(subprocess.check_output("qhosst | awk 'NR >= 4 { print $1 }'", shell=True))
    print(s)
    if len(s) == 0:
        return []
    else:
        return sorted(s.split('\n'))

def first_last_tuples_distribute_over(first_sec, last_sec, n_host):
    secs_per_job = (last_sec - first_sec + 1)/float(n_host)
    if secs_per_job < 1:
        first_last_tuples = [(i,i) for i in range(first_sec, last_sec+1)]
    else:
        first_last_tuples = [(int(first_sec+i*secs_per_job), int(first_sec+(i+1)*secs_per_job-1) if i != n_host - 1 else last_sec) for i in range(n_host)]
    return first_last_tuples

def run_distributed(stack, command, argument_type='single', kwargs_list=None, jobs_per_node=1, node_list=None, local_only=False, use_aws=False):
    """
    Distributed executing a command.
    Args:
        local_only: run on local computer instead of AWS cluster
        jobs_per_node:
        kwargs_list: either dict of lists {kA: [vA1, vA2, ...], kB: [vB1, vB2, ...]} or list of dicts [{kA:vA1, kB:vB1}, {kA:vA2, kB:vB2}, ...].
        argument_type: one of list, list2, single. If command takes one input item as argument, use "single". If command takes a list of input items as argument, use "list2". If command takes an argument called "kwargs_str", use "list".
    """
    fileLocationManager = FileLocationManager(stack)
    print('run ddddddddddddddddistrib', kwargs_list)
    if use_aws:
        execute_command('rm -f /home/ubuntu/stderr_*; rm -f /home/ubuntu/stdout_*')
    else:
        execute_command('rm -f %s; rm -f %s' % (os.path.join(fileLocationManager.mouseatlas_tmp, 'stderr_*'),
                                                os.path.join('stdout_*')))

    if local_only:
        sys.stderr.write("Run locally.\n")

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
        kwargs_list = {'dummy': [None]*n_hosts}

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
    print('point 1')
    for node_i, (fi, li) in enumerate(first_last_tuples_distribute_over(0, len(kwargs_list_as_list)-1, n_hosts)):

        temp_script = os.path.join(fileLocationManager.mouseatlas_tmp, 'runall.sh')
        temp_f = open(temp_script, 'w')

        for j, (fj, lj) in enumerate(first_last_tuples_distribute_over(fi, li, jobs_per_node)):
            print('node i j fj, lj', j, fj, lj)
            if argument_type == 'list':
                line = command % {'kwargs_str': json.dumps(kwargs_list_as_list[fj:lj+1])}
            elif argument_type == 'list2':
                line = command % {key: json.dumps(vals[fj:lj+1]) for key, vals in kwargs_list_as_dict.items()}
            elif argument_type == 'single':
                # It is important to wrap command_templates and kwargs_list_str in apostrphes.
                # That lets bash treat them as single strings.
                # Reference: http://stackoverflow.com/questions/15783701/which-characters-need-to-be-escaped-in-bash-how-do-we-know-it
                line = "%(generic_launcher_path)s %(command_template)s %(kwargs_list_str)s" % \
                       {'generic_launcher_path': os.path.join(UTILITY_DIR, 'sequential_dispatcher.py'),
                        'command_template': shell_escape(command),
                        'kwargs_list_str': shell_escape(json.dumps(kwargs_list_as_list[fj:lj+1]))
                        }

            temp_f.write(line + ' &\n')

        temp_f.write('wait')
        temp_f.close()
        os.chmod(temp_script, 0o777)

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
            print('running temp_script', temp_script)
            subprocess.run(temp_script, shell=True, stdout=stdout_f, stderr=stderr_f)
        else:
            print('qsub -V -q all.q@%(node)s -o %(stdout_log)s -e %(stderr_log)s %(script)s' % \
                  dict(node=node_list[node_i], script=temp_script, stdout_log=stdout_template % node_i, stderr_log=stderr_template % node_i))

            subprocess.call('qsub -V -q all.q@%(node)s -o %(stdout_log)s -e %(stderr_log)s %(script)s' % \
                 dict(node=node_list[node_i], script=temp_script,
                      stdout_log=stdout_template % node_i, stderr_log=stderr_template % node_i),
                 shell=True)

    sys.stderr.write('Jobs submitted. Use wait_qsub_complete() to wait for all execution to finish.\n')
