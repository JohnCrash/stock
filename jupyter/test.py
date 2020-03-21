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

"""
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
"""
def progress(i):
    print(i)
companys = stock.query("""select company_id,code,name,category,ttm,pb from company_select""")
id2companys = {}
for c in companys:
    id2companys[c[0]] = c
def isRasing(a,c,istoday):
    #istoday True可以使用xueqiu数据
    #c [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]  
    #0 id ,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw
    dMACD = a[-1,4]-a[-2,4]
    #macd在零轴附件（预计2日穿过或者已经穿过2日）,股价涨,能量线崛起
    if dMACD>0 and a[-1,1]-a[-2,1]>0 and a[-1,5]>=3 and a[-2,5]<3:
        if (a[-1,4]<0 and a[-1,4]+2*dMACD>0) or (a[-1,4]>0 and a[-1,4]-2*dMACD<0):
            return True,[{'x':[-1],'color':'magenta','linestyle':'--','linewidth':2}]
    return False,[]    
rasing,vlines = status.searchRasingCompanyStatusByRT('2020-04-20','d',isRasing,id2companys,progress)    
#status.StrongSorted([3],progress=progress,companys=companys)

#xueqiu.clearAllRT()
#status.updateRT(companys)
