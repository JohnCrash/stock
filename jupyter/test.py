"""
d1是k1的日期表,将k1和日期表date对齐
d1和date来自于loadKline的返回日期
"""
import numpy as np
import stock
import status
import shared
import xueqiu
import threading
import queue
import time

c,k,d = stock.loadKline('SH:000001')

r = stock.volumeprices(k,d)