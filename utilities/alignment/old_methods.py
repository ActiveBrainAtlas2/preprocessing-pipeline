import os, sys
import subprocess
import json

DATA_ROOTDIR = os.environ['DATA_ROOTDIR']


def execute_command(cmd, stdout=None, stderr=None):
    sys.stderr.write(cmd + '\n')

    # try:
#     from errand_boy.transports.unixsocket import UNIXSocketTransport
#     errand_boy_transport = UNIXSocketTransport()
#     stdout, stderr, retcode = errand_boy_transport.run_cmd(cmd)

#     print stdout
#     print stderr

    # import os
    # retcode = os.system(cmd)
    retcode = subprocess.call(cmd, shell=True, stdout=stdout, stderr=stderr)
    sys.stderr.write('return code: %d\n' % retcode)

    # if retcode < 0:
    #     print >>sys.stderr, "Child was terminated by signal", -retcode
    # else:
    #     print >>sys.stderr, "Child returned", retcode
    # except OSError as e:
    #     print >>sys.stderr, "Execution failed:", e
    #     raise e


def run_distributed(command, argument_type='single', kwargs_list=None, jobs_per_node=1, node_list=None, local_only=False, use_aws=False):
    run_distributed5(**locals())


def run_distributed5(command, argument_type='single', kwargs_list=None, jobs_per_node=1, node_list=None,
                     local_only=False, use_aws=False):
    """
    Distributed executing a command.

    Args:
        local_only: run on local computer instead of AWS cluster
        jobs_per_node:
        kwargs_list: either dict of lists {kA: [vA1, vA2, ...], kB: [vB1, vB2, ...]} or list of dicts [{kA:vA1, kB:vB1}, {kA:vA2, kB:vB2}, ...].
        argument_type: one of list, list2, single. If command takes one input item as argument, use "single". If command takes a list of input items as argument, use "list2". If command takes an argument called "kwargs_str", use "list".
    """

    if use_aws:
        execute_command('rm -f /home/ubuntu/stderr_*; rm -f /home/ubuntu/stdout_*')
    else:
        execute_command('rm -f %s; rm -f %s' % (os.path.join(DATA_ROOTDIR, 'mousebrainatlas_tmp', 'stderr_*'),
                                                os.path.join(DATA_ROOTDIR, 'mousebrainatlas_tmp', 'stdout_*')))

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

    create_if_not_exists(os.path.join(DATA_ROOTDIR, 'mousebrainatlas_tmp'))

    for node_i, (fi, li) in enumerate(first_last_tuples_distribute_over(0, len(kwargs_list_as_list) - 1, n_hosts)):

        temp_script = os.path.join(DATA_ROOTDIR, 'mousebrainatlas_tmp', 'runall.sh')
        temp_f = open(temp_script, 'w')

        for j, (fj, lj) in enumerate(first_last_tuples_distribute_over(fi, li, jobs_per_node)):
            if argument_type == 'list':
                line = command % {'kwargs_str': json.dumps(kwargs_list_as_list[fj:lj + 1])}
            elif argument_type == 'list2':
                line = command % {key: json.dumps(vals[fj:lj + 1]) for key, vals in kwargs_list_as_dict.iteritems()}
            elif argument_type == 'single':
                # It is important to wrap command_templates and kwargs_list_str in apostrphes.
                # That lets bash treat them as single strings.
                # Reference: http://stackoverflow.com/questions/15783701/which-characters-need-to-be-escaped-in-bash-how-do-we-know-it
                line = "%(generic_launcher_path)s %(command_template)s %(kwargs_list_str)s" % \
                       {'generic_launcher_path': os.path.join(os.environ['REPO_DIR'], 'utilities',
                                                              'sequential_dispatcher.py'),
                        'command_template': shell_escape(command),
                        'kwargs_list_str': shell_escape(json.dumps(kwargs_list_as_list[fj:lj + 1]))
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
            stdout_template = os.path.join(DATA_ROOTDIR, 'mousebrainatlas_tmp', 'stdout_%d.log')
            stderr_template = os.path.join(DATA_ROOTDIR, 'mousebrainatlas_tmp', 'stderr_%d.log')

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

    sys.stderr.write('Jobs submitted. Use wait_qsub_complete() to wait for all execution to finish.\n')


def get_node_list():
    s = subprocess.check_output("qhost | awk 'NR >= 4 { print $1 }'", shell=True).strip()
    print("qhost | awk 'NR >= 4 { print $1 }'")
    print(subprocess.check_output("qhosst | awk 'NR >= 4 { print $1 }'", shell=True))
    print(s)
    if len(s) == 0:
        return []
    else:
        return sorted(s.split('\n'))



def create_parent_dir_if_not_exists(fp):
    create_if_not_exists(os.path.dirname(fp))

def create_if_not_exists(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            sys.stderr.write('%s\n' % e)

    return path


def first_last_tuples_distribute_over(first_sec, last_sec, n_host):
    secs_per_job = (last_sec - first_sec + 1)/float(n_host)
    if secs_per_job < 1:
        first_last_tuples = [(i,i) for i in range(first_sec, last_sec+1)]
    else:
        first_last_tuples = [(int(first_sec+i*secs_per_job), int(first_sec+(i+1)*secs_per_job-1) if i != n_host - 1 else last_sec) for i in range(n_host)]
    return first_last_tuples



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
