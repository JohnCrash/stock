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
from IPython.core.interactiveshell import InteractiveShell
"""
display_pub = InteractiveShell.instance().display_pub
display_pub.publish(data='hell',metadata={})
c,k,d = stock.loadKline('SH:000001')

r = stock.volumeprices(k,d)
"""
#b,k,d = xueqiu.qqK15('SZ399001')
#c,k,d = stock.loadKline('SZ399001',5)
#stock.correctionVolume(k,d,5)
xueqiu.xueqiuK15day('SZ399001')