import logging

def init(filename):
    log = logging.getLogger('mylog')
    log.setLevel(level = logging.INFO)
    hd = logging.FileHandler(filename)
    hd.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hd.setFormatter(formatter)
    log.addHandler(hd)

def warn(*args):
    log = logging.getLogger('mylog')
    log.warning(*args)

def err(*args):
    log = logging.getLogger('mylog')
    log.error(*args)

def info(*args):
    log = logging.getLogger('mylog')
    log.info(*args)