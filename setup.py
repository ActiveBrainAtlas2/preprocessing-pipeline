# This is just a shim for `pip install -e` to work. See
#   https://setuptools.readthedocs.io/en/latest/userguide/quickstart.html#development-mode

import setuptools
setuptools.setup(name = 'pipeline',packages = ['pipeline'], package_dir = {'pipeline':'src'})

