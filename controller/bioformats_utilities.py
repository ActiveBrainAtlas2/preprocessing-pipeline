import subprocess


def get_czi_metadata(infile):
    """
    This parses the CZI file with the bioformats tool: showinf.
    :param infile: file location of the CZI file
    :return: dictionary of meta information
    """
    command = ['/usr/local/share/bftools/showinf', '-nopix', infile]
    czi_metadata_full = subprocess.check_output(command)
    czi_metadata_full = czi_metadata_full.decode("utf-8")
    # I seperate the metadata into 3 seperate sections
    czi_metadata_header = czi_metadata_full[0:czi_metadata_full.index('\nSeries #0')]
    czi_metadata_series = czi_metadata_full[0:czi_metadata_full.index('\nReading global metadata')]
    czi_metadata_global = czi_metadata_full[czi_metadata_full.index('\nReading global metadata'):]

    # This extracts the 'series' count.
    # Each series is a tissue sample at a certain resolution
    #  or an erroneous thingy
    series_count = int(czi_metadata_header[
                       czi_metadata_header.index('Series count = ') + 15:])

    # Series #0 should be the first tissue sample at full resolution.
    # Series #1 tends to be this same tissue sample at half the resolution.
    # This continues halving resolution 5-6 times in succession. We only
    # want the full resolution tissue series so we ignore those with dimensions
    # that are much smaller than expected. Valid series are checked in get_fullres_series_indices

    metadata_dict = {}

    for series_i in range(series_count):
        if series_i == series_count - 1:
            czi_metadata_series_i = czi_metadata_series[
                                    czi_metadata_series.index('Series #' + str(series_i)):]
        # Otherwise extract metadata from Series(#) to Series(#+1)
        else:
            czi_metadata_series_i = czi_metadata_series[
                                    czi_metadata_series.index('Series #' + str(series_i)):
                                    czi_metadata_series.index('Series #' + str(series_i + 1))]

        # Extract width and height
        width_height_data = czi_metadata_series_i[czi_metadata_series_i.index('Width'):
                                                  czi_metadata_series_i.index('\n\tSizeZ')]
        width, height = width_height_data.replace('Width = ', '').replace('Height = ', '').split('\n\t')
        metadata_dict[series_i] = {}
        metadata_dict[series_i]['width'] = width
        metadata_dict[series_i]['height'] = height
        # Extract number of channels
        channel_count_index = czi_metadata_series_i.index('SizeC = ') + 8
        channel_count = int(czi_metadata_series_i[channel_count_index: channel_count_index + 1])
        metadata_dict[series_i]['channels'] = channel_count

    for channel_i in range(metadata_dict[0]['channels']):
        # Extract channel names
        str_to_search = 'Information|Image|Channel|Name #' + str(channel_i + 1) + ': '
        str_index = czi_metadata_global.index(str_to_search)
        channel_name = czi_metadata_global[str_index + len(str_to_search):
                                           czi_metadata_global.find('\n', str_index)]
        metadata_dict['channel_' + str(channel_i) + '_name'] = channel_name

    return metadata_dict


def get_fullres_series_indices(metadata_dict):
    """
    This gets the valid series by looking at the size of the image available.
    :param metadata_dict: this is the dictionary retrieved from the showinf command
    :return: correct list of valid series.
    """
    fullres_series_indices = []
    series = []
    for key in metadata_dict.keys():
        try:
            int(key)
            series.append(int(key))
        except:
            # del metadata_dict[key]
            continue
    # last_series_i = max(metadata_dict.keys())
    last_series_i = max(series)
    metadata_dict = {k: metadata_dict[k] for k in series}
    series_0_width = int(metadata_dict[0]['width'])
    series_0_height = int(metadata_dict[0]['height'])

    for series_curr in metadata_dict.keys():
        # Series 0 is currently assumed to be real, fullres tissue
        if series_curr != 0:
            series_curr_width = int(metadata_dict[series_curr]['width'])
            series_prev_width = int(metadata_dict[series_curr - 1]['width'])
            series_prev_width_halved = series_prev_width / 2
            # If the curr series is about half the size of the previous series
            # this indicates that it is not a new tissue sample, just a
            # downsampled version of the previous series.
            if abs(series_curr_width - series_prev_width_halved) < 5:
                continue
            # If this series is suspisciously small, it is not likely to be fullres
            # Currently this assumed that series#0 is fullres
            if series_curr_width < series_0_width * 0.5:
                continue
        # We ignore the last two series.
        # 2nd last should be "label image"
        # last should be "macro image"
        if series_curr >= last_series_i - 2:
            continue

        fullres_series_indices.append(series_curr)

    return fullres_series_indices
