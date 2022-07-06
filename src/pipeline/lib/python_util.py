def read_file(path):
    """read text from a binary file

    Args:
        path (str): path to the file to read

    Returns:
        str: string contained in the file
    """    
    text_file = open(path, "r")
    data = text_file.read()
    text_file.close()
    return data