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
import kline
import math


companys = stock.query("select company_id,code,name,category from company_select")
coms = []
id2com = {}
i = 0
for com in companys:
    coms.append(com[1])
    id2com[com[0]] = com
    if com[1]=='SZ300173':
        print(i)
        print(com)
    i+=1
def progress(i):
    print(i)

K,D = status.updateRT(companys,progress=progress)

def code2Server(code):
    j = 0
    for i in range(0,len(companys),100):
        batch = math.floor(i/100)
        for com in companys[i:i+100]:
            if com[1]==code:
                if batch%3==0:
                    print('xueqiu',code)
                    print(K[j,:,2])
                elif batch%3==1:
                    print('sina',code)
                    print(K[j,:,2])
                else:
                    print('qq',code)
                    print(K[j,:,2])
                return
            j+=1

code2Server('SH600360')
code2Server('SZ002091')
code2Server('SH603912')
code2Server('SZ002418')
code2Server('SZ300223')
code2Server('SZ002065')
code2Server('SZ002458')
#status.StrongSorted([3],progress=progress,companys=companys)

#xueqiu.clearAllRT()
#status.updateRT(companys)
