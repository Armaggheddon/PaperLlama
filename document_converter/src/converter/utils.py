import os

def get_max_num_pages():
    return os.environ.get("MAX_PAGE_COUNT", 100)

def get_max_file_size():
    return os.environ.get("MAX_FILE_SIZE", 20_000_000)