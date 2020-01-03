import numpy as np
import stock

#返回满足条件的范围数据
def argRange(d):
    r = []
    p = not d[0]
    bi = -1
    for i in range(len(d)):
        if d[i] and not p:
            bi = i
        elif bi!=-1 and not d[i] and p:
            r.append([bi,i])
            bi = -1
        p = d[i]
    if bi != -1:
        r.append([bi,len(d)])
    return np.array(r,dtype=np.int32)

def argWhere(d):
    return np.argwhere(d).reshape(-1)

#返回,n1是短期均线,n2是长期均线
def maIndexs(k,n1,n2):
    ma1 = stock.ma(k,n1)
    ma2 = stock.ma(k,n2)
    return argWhere(ma1>ma2)

def maRange(k,n1,n2):
    ma1 = stock.ma(k,n1)
    ma2 = stock.ma(k,n2)
    return argRange(ma1>ma2)

#返回macd>0的区域
def macdIndexs(k):
    macd,_= stock.macd(k)
    return argWhere(macd>0)

def macdRange(k):
    macd,_= stock.macd(k)
    return argRange(macd>0)

#返回窄布林通道,UT表示布林宽的上限,WT表示通道最小和最大的差上限,LT表示通道的长度下限
def bollSelectRange(k,n=20,UT=0.2,LT=15):
    bo = stock.bollLineK(k,n)
    bw = stock.bollWidth(bo)
    r = argRange(bw<UT)
    R = []
    for b in r:
        if b[1]-b[0]>LT:
            R.append([b[0]-LT,b[1]])
    return np.array(R)

#将范围表示转换为索引表示
def rangeToIndexs(r):
    inds = []
    for b in r:
        inds += range(b[0],b[1])
    return np.array(inds,dtype=np.int32)

#将索引表示转换为范围表示,
def indexsToRange(inds,needSort=False):
    if needSort:
        inds = sorted(inds)
    r = []
    bi = inds[0]
    p = inds[0]+1
    for i in inds:
        if i != p+1:
            r.append([bi,p+1])
            bi = i
        p = i
    if bi != p:
        r.append([bi,p+1])
    return np.array(r,dtype=np.int32)

#价格平台,平台的宽带和股价的比例UT，LT平台长度
def priceLandRange(k,UT=0.2,LT=15):
    pass

#返回成交量大于n日均线值多少的r倍
def volumeIndexs(k,r=1.5,n=20):
    ma = stock.ma(k[:,0],n)
    return argWhere(k[:,0]/ma>r)

#返回符合量价条件的范围点
def volumePriceIndexs(k,n,r):
    pass

#索引的交集
def intersectionIndexs(a):
    for i in range(len(a)):
        if i == 0:
            p = a[i]
        else:
            p = np.intersect1d(p,a[i])
    return p

#将索引展开成bool数组，l是长度
def flatIndexs(inds,l):
    p = np.zeros((l),dtype=np.bool)
    p[inds] = True
    return p

#选择区域内的第一个索引
def rangeFirstIndexs(r,inds,n):
    p = flatIndexs(inds,n)
    R = []
    for b in r:
        for i in range(b[0],b[1]):
            if p[i]:
                R.append(i)
                break
    return np.array(R,dtype=np.int32)