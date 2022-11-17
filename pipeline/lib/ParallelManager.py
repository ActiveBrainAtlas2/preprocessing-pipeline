from concurrent.futures.process import ProcessPoolExecutor

from utilities.utilities_process import get_hostname


class ParallelManager:
    """Methods to support processing any part of pipeline (discreet function) using multiple cores
    """

    def get_nworkers(self):
        """There is little point in setting two different levels in one host
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
        if self.debug:
            for file_key in sorted(file_keys):
                function(file_key)
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                executor.map(function, sorted(file_keys))

