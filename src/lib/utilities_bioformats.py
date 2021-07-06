import subprocess

import bioformats

def get_czi_metadata(infile):
    """
    This parses the CZI file with the bioformats tool: showinf.
    :param infile: file location of the CZI file
    :return: dictionary of meta information
    """
    command = ['/usr/local/share/bftools/showinf', '-nopix', '-omexml-only', infile]
    metadata = subprocess.check_output(command).decode('utf-8')
    metadata = bioformats.OMEXML(metadata)

    # Series #0 should be the first tissue sample at full resolution.
    # Series #1 tends to be this same tissue sample at half the resolution.
    # This continues halving resolution 5-6 times in succession. We only
    # want the full resolution tissue series so we ignore those with dimensions
    # that are much smaller than expected. Valid series are checked in get_fullres_series_indices

    metadata_dict = {}
    for i in range(metadata.image_count):
        image = metadata.image(i)
        metadata_dict[i] = {}
        metadata_dict[i]['width'] = image.Pixels.SizeX
        metadata_dict[i]['height'] = image.Pixels.SizeY
        metadata_dict[i]['channels'] = image.Pixels.channel_count

    image = metadata.image(0)
    for i in range(image.Pixels.channel_count):
        metadata_dict[f'channel_{i}_name'] = image.Pixels.channel(i).Name

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
            #print(f'series_curr_width - series_prev_width_halved {series_curr_width}  {series_prev_width_halved}')
            if abs(series_curr_width - series_prev_width_halved) < 5:
                continue
            # If this series is suspisciously small, it is not likely to be fullres
            # Currently this assumed that series#0 is fullres
            if series_curr_width < series_0_width * 0.47:
                continue
        # We ignore the last two series.
        # 2nd last should be "label image"
        # last should be "macro image"
        if series_curr >= last_series_i - 2:
            continue

        fullres_series_indices.append(series_curr)

    return fullres_series_indices
