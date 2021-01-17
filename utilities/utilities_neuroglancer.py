COL_LENGTH = 1000
ROW_LENGTH = 1000
Z_LENGTH = 300
ATLAS_X_BOX_SCALE = 10
ATLAS_Y_BOX_SCALE = 10
ATLAS_Z_BOX_SCALE = 20
ATLAS_RAW_SCALE = 10


def xy_atlas2neuroglancer(xy_atlas):
    """
    0.325 is the scale for Neurotrace brains
    This converts the atlas coordinates to neuroglancer XY coordinates
    :param x: x or y coordinate
    :return: rounded integer that is in neuroglancer scale
    """
    atlas_box_center = COL_LENGTH // 2
    xy_neuroglancer = (atlas_box_center + xy_atlas) * (ATLAS_RAW_SCALE / 0.325)
    return int(round(xy_neuroglancer))

def xy_neuroglancer2atlas(xy_neuroglancer):
    """
    TODO
    0.325 is the scale for Neurotrace brains
    This converts the atlas coordinates to neuroglancer XY coordinates
    :param x: x or y coordinate
    :return: rounded xy integer that is in atlas scale
    """
    atlas_box_center = COL_LENGTH // 2
    xy_atlas = (xy_neuroglancer - atlas_box_center) / (ATLAS_RAW_SCALE / 0.325)



    return int(round(xy_atlas))



def section_atlas2neuroglancer(section):
    """
    scales the z (section) to neuroglancer coordinates
    :param section:
    :return: rounded integer in neuroglancer scale
    """
    atlas_box_center = Z_LENGTH // 2
    result = atlas_box_center + section * ATLAS_RAW_SCALE/ATLAS_Z_BOX_SCALE
    return int(round(result))


def section_neuroglancer2atlas(section):
    """
    TODO
    scales the z (section) to atlas coordinates
    :param section:
    :return: rounded integer of section in atlas coordinates
    """
    atlas_box_center = Z_LENGTH // 2
    result = atlas_box_center + section * ATLAS_RAW_SCALE/ATLAS_Z_BOX_SCALE
    return int(round(result))
