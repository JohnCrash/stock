import numpy as np
import stock
"""
基于macd的趋势
"""

"""
最小二乘法拟合直线
y = k*x+b
R 是拟合度
"""
def lastSequaresLine(x):
    a = x.mean(axis=0)
    k = ((x[:,0]-a[0])*(x[:,1]-a[1])).sum()/((x[:,0]-a[0])**2).sum()
    b = a[1]-k*a[0]
    #拟合优度,范围0-1,越靠近1拟合越好
    R = 1-((x[:,1]-k*x[:,0]-b)**2).sum()/((x[:,1]-a[1])**2).sum()
    return [k,b,R]

"""
计算和直线l平行距离为d的另外两条直线
"""
def parallelLine(l,d):
    s = d*np.sqrt(1+l[0]**2)
    return [l[0],l[1]+s],[l[0],l[1]-s]

"""
计算点到直线的距离
"""
def distancePtLine(l,x):
    return (l[0]*x[:,0]-x[:,1]+l[1])/np.sqrt(1+l[0]**2)

def k2x4(bi,ei,k):
    x = np.empty((4*(ei-bi),2))
    x[:,0] = np.repeat(np.arange(bi,ei),4)
    x[:,1] = k[bi:ei,1:5].reshape(-1)
    return x
"""
返回趋势数组
[
    [bi,ei,k,b,R,b1,b2], #bi起始位置，ei结束位置，k斜率，b斜截，R拟合度，b1表示下限斜截，b2表示上限斜截
    ...
]
m是macd，该算法基于macd的周期
"""
def trendK(k,m):
    lo,hi,pts = stock.MacdBestPt(k,m)
    lines = []
    bi = 0
    ei = 0
    for i in range(len(pts)-1):
        bi = pts[i]
        ei = pts[i+1]
        line = [bi,ei]+lastSequaresLine(k2x4(bi,ei+1,k))
        lines.append(line)
    if ei!=0 and ei<len(k):
        line = [ei,len(k)-1]+lastSequaresLine(k2x4(ei,len(k)-1,k))
        lines.append(line)
    return np.array(lines)