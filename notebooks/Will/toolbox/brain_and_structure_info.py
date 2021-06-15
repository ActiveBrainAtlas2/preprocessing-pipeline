from notebooks.Will.toolbox.data_base.sql_tools import query_brain_coms
def get_list_of_all_dk_brains():
    return ['DK39', 'DK41', 'DK43', 'DK54', 'DK55','DK52']

def get_list_of_brains_to_align():
    all_dk_brains = get_list_of_all_dk_brains()
    brains_to_align = [braini for braini in all_dk_brains if braini != 'DK52']
    return  brains_to_align

def get_common_structures():
    brains_to_align = get_list_of_brains_to_align()
    common_structures = set()
    for brain in brains_to_align:
        common_structures = common_structures | set(query_brain_coms(brain).keys())
    common_structures = list(sorted(common_structures))
    return common_structures