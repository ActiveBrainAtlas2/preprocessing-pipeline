import numpy as np
files = os.listdir(a)
widths = []
heights = []
for filei in files:
    dir = a +'/'+ filei
    width, height = get_image_size(dir)
    widths.append(int(width))
    heights.append(int(height))
widths = np.array(widths)
heights = np.array(heights)
max_width = max(widths)
max_height = max(heights)

# for filei in files:
#     dir = OUTPUT + filei
#     img = io.imread(dir)
#     img = place_image(img, dir, max_width, max_height, 0)
#     tiff.imsave(dir, img)
