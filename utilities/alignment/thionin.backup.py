def find_threshold(src):
    fig = matplotlib.figure.Figure()
    ax = matplotlib.axes.Axes(fig, (0, 0, 0, 0))
    n, bins, patches = ax.hist(src.flatten(), 360);
    del ax, fig
    min_point = np.argmin(n[:5])
    min_point = int(max(2, min_point))
    thresh = min_point * 20
    return min_point, thresh


# get oriented for comparison
img_inputs = []
img_outputs = []
file_inputs = []
titles = []
masks = []
max_width = 1400
max_height = 900
for i, file in enumerate(tqdm(files[100:110])):
    infile = os.path.join(INPUT, file)
    src = io.imread(infile)
    img_inputs.append(src)
    file_inputs.append(file)

    start_bottom = src.shape[0] - 5
    bottom_rows = src[start_bottom:src.shape[0], :]
    avg = np.mean(bottom_rows)
    bgcolor = int(round(avg))
    lower = bgcolor - 8
    upper = bgcolor + 4
    bgmask = (src >= lower) & (src <= upper)

    src[bgmask] = bgcolor
    clahe = cv2.createCLAHE(clipLimit=40.0, tileGridSize=(16, 16))
    h_src = clahe.apply(src)
    # h_src = np.copy(src)
    min_value, threshold = find_threshold(h_src)
    # print(min_value, threshold, bgcolor)
    titles.append([min_value, threshold, bgcolor])
    ret, threshed = cv2.threshold(h_src, threshold, 255, cv2.THRESH_BINARY)
    threshed = np.uint8(threshed)
    connectivity = 4
    output = cv2.connectedComponentsWithStats(threshed, connectivity, cv2.CV_32S)
    num_labels = output[0]
    labels = output[1]
    stats = output[2]
    centroids = output[3]
    row = find_main_blob(stats, h_src)
    blob_label = row[1]['blob_label']
    blob = np.uint8(labels == blob_label) * 255
    kernel10 = np.ones((10, 10), np.uint8)
    closing = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, kernel10, iterations=5)
    closing = cv2.dilate(closing, kernel10, iterations=1)
    # threshold = 1500
    # print(min_value,threshold)
    img_outputs.append(h_src)
    outpath = os.path.join(MASKED, file)
    # cv2.imwrite(outpath, closing.astype('uint8'))
    masks.append(closing)

    im_in = img_outputs[1]
    start_bottom = im_in.shape[0] - 5
    bottom_rows = im_in[start_bottom:im_in.shape[0], :]
    avg = np.mean(bottom_rows)
    bgcolor = int(round(avg)) - 1
    print(bgcolor)
    h, im_th = cv2.threshold(im_in, bgcolor, 255, cv2.THRESH_BINARY_INV)
    # Copy the thresholded image.
    im_floodfill = im_th.copy()
    # Mask used to flood filling.
    h, w = im_th.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    # Floodfill from point (0, 0)
    cv2.floodFill(im_floodfill, mask, (0, 0), 255)
    # Invert floodfilled image
    im_floodfill_inv = cv2.bitwise_not(im_floodfill)
    # Combine the two images to get the foreground.
    im_out = im_th | im_floodfill_inv
    contours, hierarchy = cv2.findContours(im_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    c = max(contours, key=cv2.contourArea)
    stencil = np.zeros(im_in.shape).astype('uint8')
    cv2.fillPoly(stencil, [c], 255)
    # result = cv2.bitwise_and(img, stencil)

    plt.figure()
    plt.imshow(stencil, cmap='gray')
    plt.show()
