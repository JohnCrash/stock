import logging

def init(filename,name='mylog'):
    log = logging.getLogger(name)
    log.setLevel(level = logging.INFO)
    hd = logging.FileHandler('d:/source/stock/jupyter/log/'+filename)
    hd.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hd.setFormatter(formatter)
    log.addHandler(hd)  
    return log