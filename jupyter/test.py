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

barrier = threading.Barrier(2)
CCC = 0
def downloadXueqiuK15(tasks,ThreadCount=10):
    results = []
    lock = threading.Lock()
    count = 0
    #t[0] = k,t[1] = c(0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw)
    def xueqiuK15(t):
        nonlocal count
        b,k_,d_ = xueqiu.xueqiuK15day(t[1][1])
        lock.acquire()
        results.append({'arg':t,'result':(b,k_,d_)})
        count-=1
        lock.release()
    for t in tasks:
        threading.Thread(target=xueqiuK15,args=((t,))).start()
        lock.acquire()
        count+=1
        lock.release()
        while count>=ThreadCount:
            time.sleep(.1)
    while count>0:
        time.sleep(.1)
    
    return results

t0 = time.time()
print('BEGIN',t0)
t1 = threading.Thread(target=f,args=('A',10))
t2 = threading.Thread(target=f,args=('B',5))
t1.start()
t2.start()
t1.join()
print('DONE',time.time())
print(time.time(),time.time()-t0)
