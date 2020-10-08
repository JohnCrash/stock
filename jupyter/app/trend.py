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

#使用全部open,high,low,close
def k2x4(bi,ei,k):
    x = np.empty((4*(ei-bi),2))
    x[:,0] = np.repeat(np.arange(bi,ei),4)
    x[:,1] = k[bi:ei,1:5].reshape(-1)
    return x

#计算line的平均趋势线,并且让平均趋势线和line的中心重回
def avgLine(lines,line):
    avg_line = [line[0],line[1],line[2],line[3],line[4]] #bi,ei,k,b,R
    n = 0
    avg_k = 0
    for l in lines:
        if line[2]*l[2]>0:
            avg_k += l[2]
            n+=1
    if n>0:
        avg_k /= n
        #让两条线的中点重合
        avg_line[3] = (line[2]-avg_k)*(line[1]+line[0])/2 + line[3]
        avg_line[2] = avg_k
    return avg_line   
"""
返回基于macd最值的趋势数组
[
    [bi,ei,k,b,R], #bi起始位置，ei结束位置，k斜率，b斜截，R拟合度
    ...
],是否为猜测趋势线 (趋势线两端都在macd相同周期)
m是macd，该算法基于macd的周期
"""
def macdTrend(k,m):
    lo,hi,pts = stock.MacdBestPt(k,m)
    lines = []
    bi = 0
    ei = 0
    length = len(pts)
    for i in range(length-1):
        bi = pts[i]
        ei = pts[i+1]
        if bi<ei:
            if i==length-2:
                line = [bi,ei]+lastSequaresLine(k2x4(bi,len(k)-1,k)) #让最后一根线使用全部数据进行拟合
            else:
                line = [bi,ei]+lastSequaresLine(k2x4(bi,ei+1,k))
            lines.append(line)
    if len(lines)==0:
        return np.array([]),[],False
    else:
        avg_lines = [avgLine(lines,line)]
    b = False
    if ei!=0 and ei<len(k)-1:
        line = [ei,len(k)]+lastSequaresLine(k2x4(ei,len(k),k))
        lines.append(line)
        avg_lines.append(avgLine(lines,line))
        b = True
    
    return np.array(lines),avg_lines,b

"""
返回最大平均偏离值
"""
def maxDeviation(k,bi,ei,line):
    x = np.arange(bi,ei+1)
    y = line[0]*x+line[1]
    p = (k[x,1]+k[x,2]+k[x,3]+k[x,4])/(4*y)-1
    return np.abs(p).max()

"""
返回符合条件的匹配
"""
def fit(k,bi,ei,dt):
    if ei>bi:
        line = lastSequaresLine(k2x4(bi,ei+1,k))
        return maxDeviation(k,bi,ei,line)<dt,line
    else:
        return False,[]
"""
返回最大偏离小于dt的趋势数组
[
    [bi,ei,k,b,R], #bi起始位置，ei结束位置，k斜率，b斜截，R拟合度
    ...
]
"""
def fractal(k,dt):
    lines = []
    bi = 0
    while bi<len(k)-1:
        ei = bi
        line=None
        for i in range(bi+1,len(k)):
            b,li = fit(k,bi,i,dt)
            if not b:
                if ei != bi:
                    lines.append([bi,ei]+line)
                    line=None
                else:
                    ei+=1
                break
            ei = i
            line = li
        if line is not None:
            lines.append([bi,ei]+line)
        bi = ei
    return np.array(lines)
"""
双向延申趋势的头部于尾部，但是偏离要小于dt
"""
def extends(k,tr,dt):
    #先做两侧拓展
    for t in tr:
        bi = int(t[0])
        ei = int(t[1])
        newbi = bi
        newline = None
        #向过去拓展
        for i in range(1,bi):
            b,li = fit(k,bi-i,ei,dt)
            if b:
                newbi = bi-i
                newline = li
            else:
                break
        newei = ei
        #向前拓展
        for i in range(ei+1,len(k)):
            b,li = fit(k,newbi,i,dt)
            if b:
                newei = i
                newline = li
            else:
                break
        if newline is not None:
            t[0] = newbi
            t[1] = newei
            t[2] = newline[0] #k
            t[3] = newline[1] #b
            t[4] = newline[2] #R
"""
将大趋势细化为小趋势,偏离小于dt
返回细化的趋势
[
    [bi,ei,k,b,R], #bi起始位置，ei结束位置，k斜率，b斜截，R拟合度
    ...
]
"""
def subdivtion(k,tr,dt):
    pass
"""
将小趋势合并成大趋势,偏离小于dt
返回更大的趋势
[
    [bi0,ei0,k0,b0,R0,bi1,ei1,k1,b1,R1], #bi起始位置，ei结束位置，k斜率，b斜截，R拟合度
    ...
]
"""
def large(k,tr,dt):
    ltr = []
    i = 0
    line = None
    while i<len(tr):
        ei = i
        for j in range(i+1,len(tr)):
            b,li = fit(k,int(tr[i][0]),int(tr[j][1]),dt)
            if not b:
                if line is not None:
                    ltr.append([i,ei]+line)
                    line = None
                else:
                    ltr.append([i,i,tr[i][2],tr[i][3],tr[i][4]])
                break
            else:
                line = li
                ei = j
        
        if line is not None:
            ltr.append([i,ei]+line)
        i = ei+1

    result = np.zeros((len(tr),10))
    for b in ltr:
        bi = tr[b[0],0]
        ei = tr[b[1],1]
        for i in range(b[0],b[1]+1):
            result[i,0] = bi
            result[i,1] = ei
            result[i,2] = b[2] #K
            result[i,3] = b[3] #B
            result[i,4] = b[4] #R
            result[i,5] = tr[i,0] #bi
            result[i,6] = tr[i,1] #ei
            result[i,7] = tr[i,2] #k
            result[i,8] = tr[i,3] #b
            result[i,9] = tr[i,4] #R

    return result
