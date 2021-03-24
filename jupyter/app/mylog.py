import sys,traceback
import logging
from . import config

def init(filename,name='mylog'):
    log = logging.getLogger(name)
    log.setLevel(level = logging.INFO)
    hd = logging.FileHandler(config.log_dir+filename)
    hd.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hd.setFormatter(formatter)
    log.addHandler(hd)  
    return log

def printe(e=None):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=3, file=sys.stdout)