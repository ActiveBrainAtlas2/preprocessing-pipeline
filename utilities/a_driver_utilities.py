import subprocess
import time

from data_manager_v2 import DataManager
from metadata import ordered_pipeline_steps

def get_current_step_from_progress_ini( stack ):
    progress_dict = DataManager.get_brain_info_progress( stack )

    for pipeline_step in ordered_pipeline_steps:
        completed = progress_dict[ pipeline_step ] in ['True','true']
        if not completed:
            return pipeline_step
    return None

def set_step_completed_in_progress_ini(stack, step):
    progress_dict = DataManager.get_brain_info_progress(stack)
    progress_dict[step] = True

    # Save PROGRESS ini
    progress_ini_to_save = {}
    progress_ini_to_save['DEFAULT'] = progress_dict

    # Get filepath and save ini
    fp = DataManager.get_brain_info_progress_fp(stack)
    save_dict_as_ini(progress_ini_to_save, fp)


def save_dict_as_ini(input_dict, fp):
    import configparser
    assert 'DEFAULT' in input_dict.keys()

    config = configparser.ConfigParser()

    for key in input_dict.keys():
        config[key] = input_dict[key]

    with open(fp, 'w') as configfile:
        config.write(configfile)


def call_and_time(command_list, completion_message=''):
    start_t = time.time()
    subprocess.call(command_list)
    end_t = time.time()

    if command_list[0] == 'python':
        print('**************************************************************************************************')
        print
        '\nScript ' + command_list[1] + ' completed. Took ', round(end_t - start_t, 1), ' seconds'
        print
        completion_message + '\n'
        print('**************************************************************************************************')
