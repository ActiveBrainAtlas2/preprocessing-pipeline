import os
import socket
from subprocess import Popen
import math


def convert_size(size_bytes: int) -> str:
    '''Function takes unformatted bytes, calculates human-readable format [with units] and returns string

    :param size_bytes:
    :type size_bytes: int
    :return: str:
    '''
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def get_hostname() -> str:
    '''Function captures local hostname [where code is executed] and returns string value

    :param None:
    :rtype: str
    '''
    hostname = socket.gethostname()
    hostname = hostname.split(".")[0]
    return hostname


def get_cpus() -> tuple[int, int]:
    '''
        Function calculates available CPU cores [for parallel processing] based on host

    :param None:
    :return: tuple[int, int]:
    '''
    nmax = 4
    usecpus = (nmax,nmax)
    cpus = {}
    cpus['muralis'] = (16,40)
    cpus['basalis'] = (10,12)
    cpus['ratto'] = (10,10)
    hostname = get_hostname()
    if hostname in cpus.keys():
        usecpus = cpus[hostname]
    return usecpus


def workershell(cmd: str) -> None:
    '''
        Set up an shell command. That is what the shell true is for.

    :param cmd: a command line program with arguments in a list
    :type cmd: str
    :return: None
    '''
    stderr_template = os.path.join(os.getcwd(), 'workershell.err.log')
    stdout_template = os.path.join(os.getcwd(), 'workershell.log')
    stdout_f = open(stdout_template, "w")
    stderr_f = open(stderr_template, "w")
    proc = Popen(cmd, shell=True, stderr=stderr_f, stdout=stdout_f)
    proc.wait()


def workernoshell(cmd: str) -> None:
    '''
    Set up an shell command. That is what the shell true is for.

    :param cmd: a command line program with arguments in a list
    :type cmd: str
    :return: None
    '''
    stderr_template = os.path.join(os.getcwd(), 'workernoshell.err.log')
    stdout_template = os.path.join(os.getcwd(), 'workernoshell.log')
    stdout_f = open(stdout_template, "w")
    stderr_f = open(stderr_template, "w")
    proc = Popen(cmd, shell=False, stderr=stderr_f, stdout=stdout_f)
    proc.wait()


def get_last_2d(data):
    '''
    Unknown - Needs more info

    :param data:
    :type data:
    :return:
    '''
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)

