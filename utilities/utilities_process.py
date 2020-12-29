import os, sys
from subprocess import Popen, check_output
from pathlib import Path

PIPELINE_ROOT = Path('.').absolute().parent
sys.path.append(PIPELINE_ROOT.as_posix())


from utilities.sqlcontroller import SqlController

SCALING_FACTOR = 0.03125


def workershell(cmd):
    """
    Set up an shell command. That is what the shell true is for.
    Args:
        cmd:  a command line program with arguments in a list
    Returns: nothing
    """
    stderr_template = os.path.join(os.getcwd(), 'workershell.err.log')
    stdout_template = os.path.join(os.getcwd(), 'workershell.log')
    stdout_f = open(stdout_template, "w")
    stderr_f = open(stderr_template, "w")
    proc = Popen(cmd, shell=True, stderr=stderr_f, stdout=stdout_f)
    proc.wait()

def workernoshell(cmd):
    """
    Set up an shell command. That is what the shell true is for.
    Args:
        cmd:  a command line program with arguments in a list
    Returns: nothing
    """
    stderr_template = os.path.join(os.getcwd(), 'workernoshell.err.log')
    stdout_template = os.path.join(os.getcwd(), 'workernoshell.log')
    stdout_f = open(stdout_template, "w")
    stderr_f = open(stderr_template, "w")
    proc = Popen(cmd, shell=False, stderr=stderr_f, stdout=stdout_f)
    proc.wait()

def test_dir(animal, dir, full=False, same_size=False):
    error = ""
    #thumbnail resolution ntb is 10400 and min size of DK52 is 16074
    #thumbnail resolution thion is 14464 and min size for MD585 is 21954
    # so 10000 is a good min size
    # min size on NTB is 8.8K
    min_size = 7000
    if full:
        min_size = min_size * SCALING_FACTOR * 1000
    sqlController = SqlController(animal)
    section_count = sqlController.get_section_count(animal)
    files = sorted(os.listdir(dir))
    if section_count == 0:
        section_count = len(files)
    widths = set()
    heights = set()
    size_checks = []
    for f in files:
        filepath = os.path.join(dir, f)
        result_parts = str(check_output(["identify", filepath]))
        results = result_parts.split()
        width, height = results[2].split('x')
        widths.add(int(width))
        heights.add(int(height))
        size = os.path.getsize(filepath)
        if size < min_size:
            error += f"File is too small: {size} {filepath} \n"
    # picked 100 as an arbitrary number. the min file count is usually around 380 or so
    if len(files) > 100:
        min_width = min(widths)
        max_width = max(widths)
        min_height = min(heights)
        max_height = max(heights)
    else:
        min_width = 0
        max_width = 0
        min_height = 0
        max_height = 0
    if section_count != len(files):
        error += f"Number of files in {dir} is incorrect.\n"
    if min_width != max_width and min_width > 0 and same_size:
       error += f"Widths are not of equal size, min is {min_width} and max is {max_width}.\n"
    if min_height != max_height and min_height > 0 and same_size:
        error += f"Heights are not of equal size, min is {min_height} and max is {max_height}.\n"
    return error



def get_last_2d(data):
    if data.ndim <= 2:
        return data
    m,n = data.shape[-2:]
    return data.flat[:m*n].reshape(m,n)

