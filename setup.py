# This is just a shim for `pip install -e` to work. See
#   https://setuptools.readthedocs.io/en/latest/userguide/quickstart.html#development-mode

from setuptools import setup, find_packages
setup(name = 'pipeline',packages = find_packages())

