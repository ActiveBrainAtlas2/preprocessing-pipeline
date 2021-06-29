import json
def get_kui_dk52_com():
    json_file_path = '/home/zhw272/programming/pipeline_utility/notebooks/Bili/data/DK52_coms_kui_detected.json'
    with open(json_file_path) as f:
        coms_dict = json.load(f)
    return coms_dict