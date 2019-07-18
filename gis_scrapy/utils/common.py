import os


def get_storage_path():
    dir_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(dir_path, 'output')
    if not os.path.exists(path):
        os.mkdir(path)
    return path
