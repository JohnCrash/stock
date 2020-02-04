"""
d1是k1的日期表,将k1和日期表date对齐
d1和date来自于loadKline的返回日期
"""
import numpy as np
import stock
import status
import shared
import xueqiu

def alignK(date,k1,d1):
    if len(k1.shape)==1:
        k = np.zeros((len(date)))
    else:
        k = np.zeros((len(date),k1.shape[1]))

    off = 0
    for i in range(len(date)):
        d = date[i][0]
        for j in range(off,len(d1)):
            if d==d1[j][0]:
                k[i] = k1[j]
                off = j+1
                break
    return k 

#stock.createKlineCache('2012-1-1')
import time
t0 = time.time()
shared.delKey("company_status_last50")
shared.delKey("company_status_date50")
d,k = status.redisStatusCache50('company_status')
print(time.time()-t0)
