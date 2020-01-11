import MySQLdb
import numpy as np
import math

"""
加载股票数据
返回的第一个数据
company{
    0 - id,
    1 - code,
    2 - name,
    3 - category,
    4 - done,
    5 - kbegin,
    6 - kend
    ...
}
kline {
    0 - volume,
    1 - open,
    2 - high,
    3 - low,
    4 - close,
    5 - macd
}
kdate {
    0 - [date,]
}
code 可以是代码或名称
period = 'd','30','15','5'
"""
def loadKline(code,period='d'):
    db = MySQLdb.connect("localhost", "root", "789", "stock", charset='utf8',port=3307 )
    if len(code)>3 and code[0]=='S' and (code[1]=='H' or code[1]=='Z'):
        if code[2]==':':
            db.query("""select * from company where code='%s'"""%code.replace(':',''))
        else:
            db.query("""select * from company where code='%s'"""%code)
    else:
        db.query("""select * from company where name='%s'"""%code)
    r = db.store_result()
    company = r.fetch_row()
    db.query("""select volume,open,high,low,close from k%s_xueqiu where id=%s"""%(period,company[0][0]))
    r = db.store_result()
    k = r.fetch_row(r.num_rows())
    if period=='d':
        db.query("""select date from k%s_xueqiu where id=%s"""%(period,company[0][0]))
    else:
        db.query("""select timestamp from k%s_xueqiu where id=%s"""%(str(period),company[0][0]))
    r = db.store_result()
    kdate = r.fetch_row(r.num_rows())
    db.close()
    kline = np.array(k).reshape(-1,5)
    return company[0],kline,kdate

"""计算指数移动平均线ema,公式来源于baidu"""
def ema(k,n):
    m = np.empty([len(k)])
    for i in range(len(k)):
        if i==0:
            m[0] = k[i,4]
        else:
            m[i] = (2*k[i,4]+(n-1)*m[i-1])/(n+1)
    return m

"""计算macd
DIF=EMA(close，12）-EMA（close，26)
DEA=EMA(DIF,9)
MACD=(DIF-DEA)*2
展开得到
MACD=224/51*EMA(close,9)-16/3*EMA(close,12)+16/17*EMA(close,26)
"""
def macd(k):
    ema9 = ema(k,9)
    ema12 = ema(k,12)
    ema26 = ema(k,26)
    emA = np.empty([len(k),3])
    emA[:,0] = ema9
    emA[:,1] = ema12
    emA[:,2] = ema26
    return 224.*ema9/51.-16.*ema12/3.+16.*ema26/17.

#k 代表k数组, m 代表macd数组 mm这里也是macd数组, i代表当前位置,n这里无意义
def macdPrediction(k,m,emA,i,n):
    if i-1<0:
        return 0,k[i,4]
    prevMacd = m[i-1]
    #ema9 = (2.*cur+8.*ema[i:i-1,0])/10.
    #ema12 = (2.*cur+10.*ema[i:i-1,1])/13.
    #ema26 = (2.*cur+25.*ema[i:i-1,2])/27.
    #macd = 224.*ema9/51.-16.*ema12/3.+16.*ema26/17. = 0
    #接出来cur等于
    ema9 = emA[i-1,0]
    ema12 = emA[i-1,1]
    ema26 = emA[i-1,2]
    cur = -(224*8.*ema9/510.-16.*11.*ema12/39.+(16.*25.)*ema26/(17.*27.))/(448./510.-32./39.+32./(17.*27.))

    #1 买入预测，0没变，-1 卖出预测
    if cur>k[i,3] and cur<k[i,2]:
        if prevMacd > 0: #卖出时预测值大于最低值
            return -1,cur
        elif prevMacd < 0: #买入时预测值小于最大值
            return 1,cur
    return 0,cur

"""
计算一般一个值的kdj
"""
def kdj(k,n=9):
    kdj = np.empty([len(k),3]) #K,D,J
    for i in range(len(k)):
        if i-n+1>=0:
            prevn = k[i-n+1:i+1]
        else:
            prevn = k[0:i+1]
        Ln = prevn.min()
        Hn = prevn.max()
        if Hn-Ln==0:
            rsv = (k[i]-Ln)*100.    
        else:
            rsv = (k[i]-Ln)*100./(Hn-Ln)
        if i>=1:
            kdj[i,0] = 2.*kdj[i-1,0]/3.+rsv/3.
            kdj[i,1] = 2.*kdj[i-1,1]/3.+kdj[i,0]/3.
        else:
            kdj[i,0] = 2.*50./3.+rsv/3.
            kdj[i,1] = 2.*50./3.+kdj[i,0]/3.            
        kdj[i,2] = 3.*kdj[i,0]-2.*kdj[i,1]
    return kdj  

"""
价格和均线的差的积分
"""      
def volumeEnergyK(k,n=20):
    ve = np.zeros((len(k)))
    ma20 = ma(k[:,0],n)
    for i in range(1,len(k)):
        ve[i] = ve[i-1]+k[i,0]-ma20[i]
    return ve

"""
对上面指标的改进
"""
def volumeEnergyK2(k,n=20):
    ve = np.zeros((len(k)))
    ma20 = ma(k[:,0],n)
    for i in range(1,len(k)):
        r = min( (k[i,3]-k[i-1,4])/k[i-1,4],(k[i,4]-k[i,1])/k[i-1,4])
        if r<0 and r<-0.05:
            ve[i] = ve[i-1]-k[i,0]+ma20[i] #股价有较大跌幅
        else:
            ve[i] = ve[i-1]+k[i,0]-ma20[i] #正常情况
    return ve

"""计算kdj
n日RSV=（Cn－Ln）/（Hn－Ln）×100
公式中，Cn为第n日收盘价；Ln为n日内的最低价；Hn为n日内的最高价。
"""
def kdjK(k,n=9):
    kdj = np.empty([len(k),3]) #K,D,J
    for i in range(len(k)):
        if i-n+1>=0:
            prevn = k[i-n+1:i+1,2:4]
        else:
            prevn = k[0:i+1,2:4]
        Ln = prevn.min()
        Hn = prevn.max()
        if Hn-Ln==0:
            rsv = (k[i,4]-Ln)*100.
        else:
            rsv = (k[i,4]-Ln)*100./ (Hn-Ln)
        if i>=1:
            kdj[i,0] = 2.*kdj[i-1,0]/3.+rsv/3.
            kdj[i,1] = 2.*kdj[i-1,1]/3.+kdj[i,0]/3.
        else:
            kdj[i,0] = 2.*50./3.+rsv/3.
            kdj[i,1] = 2.*50./3.+kdj[i,0]/3.            
        kdj[i,2] = 3.*kdj[i,0]-2.*kdj[i,1]
    return kdj

#对kdJ进行计算预测
def kdjPrediction(k,k_d,kdJ,i,N):
    if i-N<0:
        return 0,k[i,4]
    prev_K_D = k_d[i-1]
    """
    Hn = max(PrevHn,cur)
    Ln = min(PrevLn,cur)
    rsv = (cur-Ln)*100./(Hn-Ln)
    K = 2.*kdJ[i-1,0]+rsv/3.
    D = 2.*kdJ[i-1,1]+K/3.
    K-D = 0
    => rsv = (cur-min(PrevLn,cur))*100./(max(PrevHn,cur)-min(PrevLn,cur)) = 9.*kdJ[i-1,1]-6.kdJ[i-1,0]
    PrevN = k[i-N,i,2:4]
    这里简化下就是新的值没有创出新高和新低
    """
    PrevN = k[i-N:i,2:4]
    PrevHn = PrevN.max()
    PrevLn = PrevN.min()
    cur = (9.*kdJ[i-1,1]-6.*kdJ[i-1,0])*(PrevHn-PrevLn)/100. + PrevLn

    #1 买入预测，0没变，-1 卖出预测
    if cur>k[i,3] and cur<k[i,2]:
        if prev_K_D > 0: #卖出时预测值大于最低值
            return -1,cur
        elif prev_K_D < 0: #买入时预测值小于最大值
            return 1,cur
    return 0,cur    

"""计算均线 n 表示多少日均线"""
def ma(k,n):
    m = np.empty(len(k))
    for i in range(len(k)):
        if i-n+1>=0:
            m[i] = k[i-n+1:i+1].sum()/n
        else:
            m[i] = k[0:i+1].sum()/(i+1)
    return m

"""计算均线 n 表示多少日均线"""
def maK(k,n):
    m = np.empty(len(k))
    for i in range(len(k)):
        if i-n+1>=0:
            m[i] = k[i-n+1:i+1,4].sum()/n
        else:
            m[i] = k[0:i+1,4].sum()/(i+1)
    return m

"""计算指定范围的均线值"""
def maRangeK(k,n,bi,ei):
    m = np.empty(ei-bi)
    x = np.arange(bi,ei)
    for i in range(bi,ei):
        if i-n+1>=0:
            m[i-bi] = k[i-n+1:i+1,4].sum()/n
        else:
            m[i-bi] = k[0:i+1,4].sum()/(i+1)
    return x,m    
"""
计算m的切线斜率
"""
def SlopeRates(m):
    r = np.empty(len(m))
    r[0] = 0
    r[1:len(m)] = m[1:len(m)]-m[0:len(m)-1]
    return r

"""
单纯的计算boll
"""
def boll(k,n=20):
    mid = ma(k,n)
    """计算标准差"""
    MD = np.empty(len(k))
    for i in range(len(k)):
        MA = mid[i]
        if i-n+1>=0:
            MD[i] = np.sqrt(((k[i-n+1:i+1]-MA)**2).sum()/n)
        else:
            MD[i] = np.sqrt(((k[0:i+1]-MA)**2).sum()/(i+1))
    MB = mid
    UP = MB+2*MD
    DN = MB-2*MD
    return np.hstack((DN.reshape(-1,1),MB.reshape(-1,1),UP.reshape(-1,1))) 
"""
计算BOLL线
"""
def bollLineK(k,n=20):
    mid = maK(k,n)
    """计算标准差"""
    MD = np.empty(len(k))
    for i in range(len(k)):
        MA = mid[i]
        if i-n+1>=0:
            MD[i] = np.sqrt(((k[i-n+1:i+1,4]-MA)**2).sum()/n)
        else:
            MD[i] = np.sqrt(((k[0:i+1,4]-MA)**2).sum()/(i+1))
    MB = mid
    UP = MB+2*MD
    DN = MB-2*MD
    return np.hstack((DN.reshape(-1,1),MB.reshape(-1,1),UP.reshape(-1,1)))

"""
计算BOLL线的极限宽
WIDTH=（布林上限值-布林下限值）/布林股价平均值
"""
def bollWidth(b):
    return ((b[:,2]-b[:,0]))/b[:,1]

"""
计算MACD周期内的最低点和最高点
m 为macd数组
返回最低点的数组，最高点数组
"""
def MacdBestPt(k,m):
    minpts = []
    maxpts = []
    pts = []
    prev = m[0]
    minx = 10*k[0,2]
    mini = 0
    maxx = -minx
    maxi = 0
    for i in range(len(m)):
        if prev*m[i]>0:
            if m[i] < 0:
                if k[i,3]<minx: #low
                    minx = k[i,3]
                    mini = i
            else:
                if k[i,2]>maxx:
                    maxx = k[i,2] #high
                    maxi = i
        else:
            if m[i]>0:
                minpts.append(mini)
                pts.append(mini)
            else:
                maxpts.append(maxi)
                pts.append(maxi)
            minx = k[i,3]
            mini = i
            maxx = k[i,2]
            maxi = i
        prev = m[i]
    if mini!=maxi:
        if m[-1]<0:
            minpts.append(mini)
            pts.append(mini)
        else:
            maxpts.append(maxi)
            pts.append(maxi)
    return np.array(minpts),np.array(maxpts),np.array(pts)  

"""
将k进行合并，例如日k合并为周k，该方法不进行周对齐，精确的方法使用weekK
"""
def mergeK(k,n):
    m = len(k)%n
    L = math.floor(len(k)/n)
    l = L+(1 if m!=0 else 0)
    w = np.zeros((l,5))
    for i in range(L):
        w[i,0] = k[i*n:i*n+n,0].sum() #volume
        w[i,1] = k[i*n,1] #open
        w[i,2] = k[i*n:i*n+n,2].max() #high
        w[i,3] = k[i*n:i*n+n,3].min() #low
        w[i,4] = k[i*n+n-1,4] #close
    if m>0:
        w[-1,0] = k[L*n:,0].sum() #volume
        w[-1,1] = k[L*n,1] #open
        w[-1,2] = k[L*n:,2].max() #high
        w[-1,3] = k[L*n:,3].min() #low
        w[-1,4] = k[-1,4] #close
    return w

"""
将数据d放大到L的长度，中间用临近相同数据填充
"""
def scaleTo1d(d,L):
    n = len(d)
    s = L/n - math.floor(L/n)
    if s<0.5:
        N = math.floor(L/n)
    else:
        N = math.floor(L/n)+1
    
    p = np.empty((math.ceil(L/N),N))
    for i in range(N):
        p[:,i] = d
    a = p.reshape(-1)
    return a[0:L]

#两个日期在同一个周
def issameweek(d0,d1):
    if d1>d0:
        dt = d1-d0
        return 7-d0.weekday()>dt.days #0,1,2,3,4,5,6
    else:
        dt = d0-d1
        return 7-d1.weekday()>dt.days #0,1,2,3,4,5,6
"""
计算周K,date是日期
返回
[
    [volume,open,high,low,close,bi,ei], #bi,ei是原来的起始和结束(包括结束)
    ...
]
"""
def weekK(k,date):
    wk = []
    assert len(k)==len(date)
    i = 0
    n = len(k)
    while i<n:
        ei = i
        for j in range(i+1,n):
            if not issameweek(date[i][0],date[j][0]):
                ei = j-1
                break
            else:
                ei = j
        wk.append([k[i:ei+1,0].sum(),k[i,1],k[i:ei+1,2].max(),k[i:ei+1,3].min(),k[ei,4],i,ei])
        i = ei+1
    if wk[-1][6]!=n-1:
        i = n-1
        ei = n-1
        wk.append([k[i:ei+1,0].sum(),k[i,1],k[i:ei+1,2].max(),k[i:ei+1,3].min(),k[ei,4],i,ei])
    return np.array(wk)

"""
将周数据放大到日数据
wk是周K,从weekK返回 ， m是周ma,macd,或者kdj,
"""
def weekToDay(wk,m):
    assert len(wk)==len(m)
    assert wk[0,5]==0
    n = int(wk[-1,6])+1 #展开后的尺寸
    if len(m.shape)==1:
        dm = np.zeros((n))
    elif len(m.shape)==2:
        dm = np.zeros((n,m.shape[1]))
    else:
        raise ValueError("m只能是一维或者二维数组")

    for i in range(len(wk)):
        b = wk[i]
        bi = int(b[5]) #bi
        ei = int(b[6]) #ei
        dm[bi:ei+1] = np.repeat(m[i:i+1],ei-bi+1,axis=0)
    return dm

"""
d1是k1的日期表,将k1和日期表date对齐
d1和date来自于loadKline的返回日期
"""
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
