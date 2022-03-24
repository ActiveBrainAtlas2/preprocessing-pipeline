import os
from sqlalchemy import false
import yaml
import multiprocessing
import socket
import sys
from multiprocessing.pool import Pool
from lib.utilities_process import workernoshell
from concurrent.futures.process import ProcessPoolExecutor
from multiprocessing import Pool
import copy

class ParallelManager:
    def load_parallel_settings(self):
        dirname = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..','..'))
        file_path = os.path.join(dirname, 'parallel_settings.yaml')
        if os.path.exists(file_path):
            with open(file_path) as file:
                self.parallel_settings = yaml.load(file, Loader=yaml.FullLoader)
            assert self.parallel_settings['name'] == self.hostname
        else:
            ncpu = multiprocessing.cpu_count()
            host = self.hostname
            self.parallel_settings = dict(   name = host,
                                        create_tifs= (ncpu,ncpu),
                                        create_preps = (ncpu,ncpu),
                                        create_mask = (ncpu,ncpu),
                                        create_clean = (ncpu,ncpu),
                                        create_aligned = (ncpu,ncpu),
                                        create_histograms = (ncpu,ncpu),
                                        create_neuroglancer = (ncpu,ncpu),
                                        create_downsamples = (ncpu,ncpu))
            with open(r'E:\data\store_file.yaml', 'w') as file:
                documents = yaml.dump(self.parallel_settings, file_path)
            
    def get_hostname(self):
        hostname = socket.gethostname()
        hostname = hostname.split(".")[0]
        return hostname

    def get_nworkers(self,downsample = True):
        function_name = sys._getframe(1).f_code.co_name
        nworkers = eval(self.parallel_settings[function_name])
        if downsample:
            return nworkers[1]
        else:
            return nworkers[0]
    
    def run_commands_in_parallel_with_shell(self,commands,workers):
        if self.debug:
            print('debugging with single core')
            for command in commands:
                workernoshell(command)
        else:
            with Pool(workers) as p:
                p.map(workernoshell, commands)
        
    def run_commands_in_parallel_with_executor(self,file_keys,workers,function):
        if self.function_belongs_to_a_pipeline_object(function):
            function = self.make_picklable_copy_of_function(function)
        if self.debug:
            print('debugging with single core')
            for file_key in file_keys:
                function(file_key)
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                executor.map(function, sorted(file_keys))

    def function_belongs_to_a_pipeline_object(self,function):
        if not hasattr(function,'__self__'):
            return False
        else:
            return type(function.__self__) == type(self)
    
    def make_picklable_copy_of_function(self,function):
        object = copy.copy(function.__self__)
        del object.sqlController
        return getattr(object,function.__name__)