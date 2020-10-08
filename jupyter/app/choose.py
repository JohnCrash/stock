import numpy as np
import stock
import matplotlib.pyplot as plt

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
    macd = stock.macd(k)
    return argWhere(macd>0)

def macdRange(k):
    macd = stock.macd(k)
    return argRange(macd>0)

"""
返回窄布林通道,UT表示布林宽的上限,WT表示通道最小和最大的差上限,LT表示通道的长度下限
"""
def bollSelectRange(k,n=20,UT=0.2,LT=15):
    bo = stock.bollLineK(k,n)
    bw = stock.bollWidth(bo)
    r = argRange(bw<UT)
    R = []
    for b in r:
        if b[1]-b[0]>LT: 
            R.append([b[0]+LT,b[1]])
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
def volumeMaIndexs(k,r=1.5,n=20):
    ma = stock.ma(k[:,0],n)
    return argWhere(k[:,0]/ma>r)

#价格必须站上n日均线上
def priceMaIndexs(k,n=20):
    ma = stock.maK(k,n)
    return argWhere(k[:,4]>ma)

#价格增长
def priceGrowIndexs(k):
    g = k[:,4]-k[:,1]
    return argWhere(g>0)

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

#将买入点索引buy和卖出点索引sell，匹配成完整的交易
def buySellMatch(buy,sell):
    p = flatIndexs(sell,sell.max()+1)
    t = []
    buyL = len(buy)
    for i in range(buyL):
        inx = buy[i]
        nex = buy[i+1] if i+1<buyL else len(p)
        for j in range(inx,min(nex,len(p))):
            if p[j]:
                t.append([inx,j])
                break
    return np.array(t,dtype=np.int32)

#计算买卖获利表
def buySellReturnRate(k,t):
    return k[t[:,1],4]/k[t[:,0],4]

def minMaxLength(t):
    minx = 9999999
    mini = 0
    maxx = 0
    maxi = 0
    for i in range(len(t)):
        v = t[i]
        if maxx < len(v):
            maxx = len(v)
            maxi = i
        if minx > len(v):
            minx = len(v)
            mini = i
    return minx,mini,maxx,maxi

#t是交易买入点和卖出点对,数组
def analysisBuySell(company,k,t):
    wr = []
    minx,mini,maxx,maxi = minMaxLength(t)

    for i in range(len(t)):
        wr.append(len(t[i]))

    gs_kw = dict(width_ratios=wr, height_ratios=[1])
    fig, axs = plt.subplots(1, len(t),figsize=(30,5),sharey=True,gridspec_kw = gs_kw)
    fig.subplots_adjust(wspace=0.01)
    axs[0].set_title('%s %s'%(company[2],company[1]))
    R = []
    for i in range(len(t)):
        p = t[i]
        r = buySellReturnRate(k,p)
        R.append(r)
        n = len(r)
        print('平均收益',r.mean(),'成功率',(r>1).sum()/len(r))
        axs[i].plot(np.arange(n),r)
        axs[i].axhline(r.mean(),color='red')
        axs[i].axhline(1,color='black')

    r = np.zeros((maxx-minx))
    s = np.zeros((maxx-minx))
    for i in range(maxx-minx):
        r[i] = R[maxi][i:i+minx].mean()
        s[i] = (R[maxi][i:i+minx]>1).sum()/minx
    print('平移最佳平均收益：',r.max(),'平移最佳成功率：',s.max())