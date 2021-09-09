__author__ = "Zhongkai Wu"
import subprocess
from lib.utilities_process import workershell

class GimpInterface():
    """GimpInterface [a class that runs gimp python scripts from command line]
    """
    def __init__(self):
        """__init__ [starting the command string to run gimp without GUI and specifies the use of python-fu]
        """
        self.command = []
        self.init_script_lines()
        self.command.append("gimp") 
        self.command.append("-idf")
        self.command.append("--batch-interpreter")
        self.command.append("python-fu-eval")
    
    def init_script_lines(self):
        self.script_lines = []
    
    def add_batch_script(self):
        """add_batch_script [adds a -b option to the command line and automatically deals with quotes and line changes]

        :param script_lines: [list of strings containing gimp python command to run]
        :type script_lines: [list]
        """
        self.command.append("-b")
        script = "'"
        for line in self.script_lines:
            script += line.replace("'",'"') +";"
        script = script[:-1]
        script += "'"
        self.init_script_lines()
        self.command.append(script)

    def import_custome_library(self,library_path,library_name):
        """import_custome_library [adds the python fu library to path and import it as a module]

        :param library_path: [path to custom python fu library]
        :type library_path: [str]
        :param library_name: [python fu library name]
        :type library_name: [str]
        """
        library_path = self.quote_string_input(library_path)
        self.script_lines.append(f"import sys")
        self.script_lines.append(f"sys.path.append({library_path})")
        self.script_lines.append(f"import {library_name}")
        self.library_name = library_name
    
    def call_function_from_library(self,library_name,function,arguments):
        script_line = f"{library_name}.{function}("
        for key,value in arguments.items():
            script_line += f"{key} = {value} ,"
        script_line = script_line[:-1]
        script_line += ")"
        self.script_lines.append(script_line)

    def create_xcf(self,tif_path,mask_path,xcf_path):
        tif_path = self.quote_string_input(tif_path)
        mask_path = self.quote_string_input(mask_path)
        xcf_path = self.quote_string_input(xcf_path)
        arguments = {}
        arguments["tif_path"]  = tif_path
        arguments["mask_path"] = mask_path
        arguments["xcf_path"]  = xcf_path
        self.call_function_from_library(self.library_name,"test_create_xcf",arguments)
    
    def save_mask(self,mask_path,xcf_path):
        mask_path = self.quote_string_input(mask_path)
        xcf_path = self.quote_string_input(xcf_path)
        arguments = {}
        arguments["mask_path"]  = mask_path
        arguments["xcf_path"] = xcf_path
        self.call_function_from_library(self.library_name,"test_create_tif",arguments)
    
    def get_command(self):
        return " ".join(self.command)

    def print_command(self):
        command = self.get_command()
        print(command)
    
    def print_command_readable(self):
        for arg in self.command:
            if ';' in arg:
                lines = arg.split(';')
                for linei in lines:
                    print(linei)
            else:
                print(arg)
    
    def execute(self):
        self.command.append('-b') 
        self.command.append("'pdb.gimp_quit(1)'")
        report = subprocess.run(self.get_command(),shell = True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        return report

    def quote_string_input(self,string):
        return "'" + string + "'"