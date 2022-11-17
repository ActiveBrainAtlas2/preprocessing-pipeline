# from skimage import io
# import os, math
# import numpy as np
# from subprocess import check_output

#ALL FUNCTIONS IN THE FILE ARE DEPRECATED AS OF 4-NOV-2022


# def read_image(file_path):
#     try:
#         img = io.imread(file_path)
#     except IOError as e:
#         errno, strerror = e.args
#         print(f'Could not open {file_path} {errno} {strerror}')
#     return img

# def get_image_size(filepath):
#     result_parts = str(check_output(["identify", filepath]))
#     results = result_parts.split()
#     width, height = results[2].split('x')
#     return int(width), int(height)

# def get_max_image_size(folder_path):
#     size = []
#     for file in os.listdir(folder_path):
#         filepath = folder_path+'/'+file
#         width,height = get_image_size(filepath)
#         size.append([int(width),int(height)])
#     return np.array(size).max(axis = 0)


# def convert_size(size_bytes):
#     if size_bytes == 0:
#         return "0B"
#     size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
#     i = int(math.floor(math.log(size_bytes, 1024)))
#     p = math.pow(1024, i)
#     s = round(size_bytes / p, 2)
#     return "%s %s" % (s, size_name[i])
