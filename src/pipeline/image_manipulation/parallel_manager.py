"""This module helps use multiple processes (cores)
to process multiple images simultaneously.
"""
from concurrent.futures.process import ProcessPoolExecutor

from utilities.utilities_process import get_hostname


class ParallelManager:
    """Methods to support processing any part of pipeline (discreet function) using multiple cores
    """

    def get_nworkers(self):
        """Get the number of cores to use per workstation. The same
        number is used for both downsampled and full resolution images.
        There is little point in setting two different levels in one host.
        Much effort was used to set these numbers.
        """
        usecpus = 4
        cpus = {}
        cpus['mothra'] = 2
        cpus['godzilla'] = 2
        cpus['muralis'] = 10
        cpus['basalis'] = 4
        cpus['ratto'] = 4
        hostname = get_hostname()
        if hostname in cpus.keys():
            usecpus = cpus[hostname]
        return usecpus

    def run_commands_concurrently(self, function, file_keys, workers):
        """This method uses the ProcessPoolExecutor library to run
        multiple processes at the same time. It also has a debug option.
        This is helpful to show errors on stdout. 

        :param function: the function to run
        :param file_keys: tuple of file information
        :param workers: integer number of workers to use
        """
        
        if self.debug:
            for file_key in sorted(file_keys):
                function(file_key)
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                executor.map(function, sorted(file_keys))
