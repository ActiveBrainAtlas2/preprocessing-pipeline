#!/usr/bin/env python

import argparse
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""Align consecutive images. Possible bad alignment pairs are written into a separate file.
Usage 1: align_compose.py in.ini --op from_none_to_aligned
"""
)

parser.add_argument("input_spec", type=str, help="input specifier. ini")
parser.add_argument("--op", type=str, help="operation id")

args = parser.parse_args()

from utilities.utilities2015 import execute_command

execute_command('python align_v3.py %s --op %s' % (args.input_spec, args.op))
execute_command('python compose_v3.py %s --op %s' % (args.input_spec, args.op))
