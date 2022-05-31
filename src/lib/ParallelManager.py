import os
from sqlalchemy import false
import yaml
import multiprocessing
import socket
import sys
from multiprocessing.pool import Pool
from abakit.lib.utilities_process import workernoshell
from concurrent.futures.process import ProcessPoolExecutor
from multiprocessing import Pool
import copy

class ParallelManager:
    def load_parallel_settings(self):
        """Loads default number of cores to use according to specified function
        """        
        dirname = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..','..'))
        file_path = os.path.join(dirname, 'parallel_settings.yaml')
        ncores = os.cpu_count()
        if os.path.exists(file_path):
            with open(file_path) as file:
                self.parallel_settings = yaml.load(file, Loader=yaml.FullLoader)
            assert self.parallel_settings['name'] == self.hostname
        else:
            host = self.hostname
            self.parallel_settings = dict(name = host,
                                        extract_tifs_from_czi= 4,
                                        create_web_friendly_image = 4,
                                        make_full_resolution = 4,
                                        make_low_resolution = ncores,
                                        make_histogram = ncores,
                                        create_full_resolution_mask = 4,
                                        create_downsampled_mask = ncores,
                                        parallel_create_cleaned = (4,ncores),
                                        align_images = (4,ncores),
                                        create_neuroglancer = (4,ncores),
                                        apply_QC_to_full_resolution_images = 4)

            with open(file_path, 'w') as file:
                documents = yaml.dump(self.parallel_settings, file)
            
    def get_hostname(self):
        hostname = socket.gethostname()
        hostname = hostname.split(".")[0]
        return hostname

    def get_nworkers(self):
        function_name = sys._getframe(1).f_code.co_name
        nworkers = self.parallel_settings[function_name]
        if type(nworkers) != int:
            if self.downsample:
                return nworkers[0]
            else:
                return nworkers[1]
        else:
            return nworkers
    
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
            for file_key in zip(*file_keys):
                function(*file_key)
        else:
            with ProcessPoolExecutor(max_workers=workers) as executor:
                executor.map(function, *file_keys)

    def run_commands_in_parallel_with_multiprocessing(self,file_keys,workers,function):
        if self.function_belongs_to_a_pipeline_object(function):
            function = self.make_picklable_copy_of_function(function)
        if self.debug:
            print('debugging with single core')
            for file_key in zip(*file_keys):
                function(*file_key)
        else:
            processes = []
            file_keys = list(zip(*file_keys))
            i=0
            for _ in range(workers):
                p = multiprocessing.Process(target=function, args = file_keys[i])
                p.start()
                processes.append(p) 
                i+=1

    def function_belongs_to_a_pipeline_object(self,function):
        if not hasattr(function,'__self__'):
            return False
        else:
            return type(function.__self__) == type(self)
    
    def make_picklable_copy_of_function(self,function):
        object = copy.copy(function.__self__)
        del object.sqlController
        return getattr(object,function.__name__)