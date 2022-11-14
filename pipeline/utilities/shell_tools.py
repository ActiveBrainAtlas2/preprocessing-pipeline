import os
from subprocess import Popen
import math


def convert_size(size_bytes: int) -> str:
    """Function takes unformatted bytes, calculates human-readable format [with units] and returns string

    :param size_bytes:
    :type size_bytes: int
    :return: str:
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def workershell(cmd: str) -> None:
    """Set up an shell command. That is what the shell true is for.

    :param cmd: a command line program with arguments in a list
    :type cmd: str
    :return: None
    """

    stderr_template = os.path.join(os.getcwd(), 'workershell.err.log')
    stdout_template = os.path.join(os.getcwd(), 'workershell.log')
    stdout_f = open(stdout_template, "w")
    stderr_f = open(stderr_template, "w")
    proc = Popen(cmd, shell=True, stderr=stderr_f, stdout=stdout_f)
    proc.wait()


def workernoshell(cmd: str) -> None:
    """Set up an shell command. That is what the shell true is for.

    :param cmd: a command line program with arguments in a list
    :type cmd: str
    :return: None
    """

    stderr_template = os.path.join(os.getcwd(), 'workernoshell.err.log')
    stdout_template = os.path.join(os.getcwd(), 'workernoshell.log')
    stdout_f = open(stdout_template, "w")
    stderr_f = open(stderr_template, "w")
    proc = Popen(cmd, shell=False, stderr=stderr_f, stdout=stdout_f)
    proc.wait()


