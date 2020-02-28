import logging

logname = 'mylog'
def init(filename,name='mylog'):
    logname = name
    log = logging.getLogger(logname)
    log.setLevel(level = logging.INFO)
    hd = logging.FileHandler(filename)
    hd.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hd.setFormatter(formatter)
    log.addHandler(hd)

def warn(*args):
    global logname
    log = logging.getLogger(logname)
    log.warning(*args)

def err(*args):
    global logname
    log = logging.getLogger(logname)
    log.error(*args)

def info(*args):
    global logname
    log = logging.getLogger(logname)
    log.info(*args)