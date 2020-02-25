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
from datetime import datetime,date,timedelta
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
#print(xueqiu.from2now(11,30,5))
#c,k,d = stock.loadKline('SZ399001',15)
#b,k,d = xueqiu.appendK('SZ399001',15,k,d)
#b,d = xueqiu.xueqiuK5('SZ399001',96)
#print(d)
#xueqiu.K('SH000001',15,16)
"""
for i in range(5):   
    if b:
        print(s,d[0],d[-1],'\n')
    else:
        print('error\n')
"""        
#print(xueqiu.K('SZ399001',5,96))
print(xueqiu.nextKDate(datetime(2020,2,25,10,55),5))
print(xueqiu.from2now(10,55,5))
print(xueqiu.k5date)
print(xueqiu.k15date)
#r = status.StrongSorted([5])
#print(r)
#shared.delKey("company_status_last50")
#shared.delKey("company_status_date50")
#def progress(e):
#    pass
#status.update_status_begin(date(2020,2,21),False,progress)