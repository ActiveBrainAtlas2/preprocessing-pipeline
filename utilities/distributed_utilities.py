import os
import sys

from metadata import (ENABLE_UPLOAD_S3, ENABLE_DOWNLOAD_S3,
                      HOST_ID,
                      S3_DATA_BUCKET, S3_RAWDATA_BUCKET, ROOT_DIR)
from utilities2015 import execute_command

default_root = dict(localhost='/home/yuncong',
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
