import os
from subprocess import Popen, check_output

from utilities.alignment_utility import SCALING_FACTOR
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController



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

def test_dir(animal, dir, resolution):
    error = ""
    #thumbnail resolution ntb is 10400 and min size of DK52 is 16074
    #thumbnail resolution thion is 14464 and min size for MD585 is 21954
    # so 10000 is a good min size
    min_size = 10000
    #if 'full' in resolution:
    #    min_size = SCALING_FACTOR * 10
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
            error += f"File is too small {f}"
    min_width = min(widths)
    max_width = max(widths)
    min_height = min(heights)
    max_height = max(heights)
    if section_count != len(files):
        error += "Number of files is incorrect.\n"
    if min_width != max_width:
       error += f"Widths are not of equal size, min is {min_width} and max is {max_width}.\n"
    if min_height != max_height:
        error += f"Heights are not of equal size, min is {min_height} and max is {max_height}.\n"
    print(sorted(size_checks))
    return error
