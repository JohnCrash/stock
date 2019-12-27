import MySQLdb
import numpy as np

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
    db.query("""select volume,open,high,low,close,macd from k%s_xueqiu where id=%s"""%(period,company[0][0]))
    r = db.store_result()
    k = r.fetch_row(r.num_rows())
    if period=='d':
        db.query("""select date from k%s_xueqiu where id=%s"""%(period,company[0][0]))
    else:
        db.query("""select timestamp from k%s_xueqiu where id=%s"""%(str(period),company[0][0]))
    r = db.store_result()
    kdate = r.fetch_row(r.num_rows())
    db.close()
    kline = np.array(k).reshape(-1,6)
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
    return 224.*ema9/51.-16.*ema12/3.+16.*ema26/17.,emA

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
        
"""计算kdj
n日RSV=（Cn－Ln）/（Hn－Ln）×100
公式中，Cn为第n日收盘价；Ln为n日内的最低价；Hn为n日内的最高价。
"""
def kdj(k,n):
    kdj = np.empty([len(k),3]) #K,D,J
    for i in range(len(k)):
        if i-n+1>=0:
            prevn = k[i-n+1:i+1,2:4]
        else:
            prevn = k[0:i+1,2:4]
        Ln = prevn.min()
        Hn = prevn.max()
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
def boll(k,n):
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
def bollLineK(k,n):
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
            else:
                maxpts.append(maxi)
            minx = k[i,3]
            mini = i
            maxx = k[i,2]
            maxi = i
        prev = m[i]
    return np.array(minpts),np.array(maxpts)        
    