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

status.StrongSortedRT([3],progress=progress,companys=companys)
"""

"""
def progress(i):
    print(i)
companys = stock.query("select company_id,code,name,category,ttm,pb from company_select")
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
"""

#xueqiu.clearAllRT()
#status.updateRT(companys)

#xueqiu.sinaFlowRT()
#print('Done')
#status.saveflow()
"""
def process(i):
    pass
print("保存资金流向到数据库...")
xueqiu.sinaFlowRT()
status.saveflow()
print("开始更新数据库...")
status.update_status(process)
print("更新完成。") 
"""
#status.showzdt(bi='2019-01-02',ei='2019-10-01')
b,seqs = shared.fromRedis('runtime_sequence')
for s in seqs:
    b,p = shared.numpyFromRedis("rt%d"%s)
    if b:
        shared.numpyToRedis(p,"rt%d"%s,ex=4*24*3600)