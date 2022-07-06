import numpy as np

def runlength_encoding_for_binary_masks(mask):
    line_width = len(mask[0])
    compressed_mask = []
    boolean_to_string = lambda x: 'T' if x else 'F'
    for linei in mask:
        compressed_line = []
        starting_character = linei[0]
        index_of_change = np.where(linei[:-1] != linei[1:])[0] + 1
        index_of_change[1:] = index_of_change[1:]-index_of_change[:-1]
        compressed_line.append(starting_character)
        for change in index_of_change:
            starting_character = not starting_character
            compressed_line.append(change)
        compressed_line.append(line_width-sum(index_of_change))
        compressed_mask.append(compressed_line)
    return compressed_mask
    
def run_length_decoding_for_binary_masks(compressed_mask):
    mask = []
    line_width = sum(compressed_mask[0])
    for linei in compressed_mask:
        starting_state = linei[0]
        line = np.ones(line_width)*starting_state
        index_of_change = np.cumsum(linei[1:])
        starts = index_of_change[::2]
        ends = index_of_change[1::2]
        if len(starts)!=len(ends):
            ends = np.append(ends,[line_width])
        for i in range(len(starts)):
            line[starts[i]:ends[i]]=(not starting_state)*1
        mask.append(line)
    return np.array(mask)==1
