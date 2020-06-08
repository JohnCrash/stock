import MySQLdb
import numpy as np
import math
from datetime import date,datetime
import shared
import config

def isTransTime(t=None):
    if t is None:
        t = datetime.today()
    return ((t.hour==9 and t.minute>=30) or t.hour==10 or (t.hour==11 and t.minute<30) or (t.hour>=13 and t.hour<15)) and t.weekday()>=0 and t.weekday()<5

#判断今天是不是可以交易
def isTransDay():
    t = datetime.today()
    if t.weekday()>=0 and t.weekday()<5:
        b,isb = shared.fromRedis('istransday_%d_%d'%(t.month,t.day))
        if b:
            return isb
        return True
    else:
        return False

def dateString(t):
    return '%s-%s-%s'%(t.year,t.month,t.day)
def timeString(t):
    return '%s-%s-%s %s:%s:%s'%(t.year,t.month,t.day,t.hour,t.minute,t.second)
gdb = None

def opendb():
    global gdb
    if gdb is None:
        gdb = MySQLdb.connect("localhost", config.mysql_user, config.mysql_pwd, "stock", charset='utf8',port=config.mysql_port )

def closedb():
    global gdb
    if gdb is not None:
        gdb.close()
        gdb = None

def query(s):
    global gdb
    if gdb is None:
        opendb()
    gdb.query(s)
    r = gdb.store_result()
    return r.fetch_row(r.num_rows())

def execute(s):
    global gdb
    cursor = gdb.cursor()
    if gdb is None:
        opendb()    
    try:
        cursor.execute(s)
        gdb.commit()
    except Exception as e:
        print(e,s)
        gdb.rollback()

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
after 载入该日期之后的数据
ei 之前的
expire 缓存过期时间（秒）
"""
def loadKline(code,period='d',after=None,ei=None,expire=None):
    #if len(code)>3 and code[0]=='S' and (code[1]=='H' or code[1]=='Z'):
    #    if code[2]==':':
    #        company = query("""select * from company where code='%s'"""%code.replace(':',''))
    #    else:
    #        company = query("""select * from company where code='%s'"""%code)
    #else:
    #    company = query("""select * from company where name='%s'"""%code)
    """
    如果使用缓存先尝试使用缓存数据
    """
    if expire is not None and period=='d':
        b1,kline = shared.numpyFromRedis(code+'_K')
        b2,kdate = shared.fromRedis(code+'_D')
        b3,company = shared.fromRedis(code)
        if b1 and b2 and b3:
            return company[0],kline,kdate
    if expire is not None: #如果使用缓存则加载全部数据
        after = None
    """
    这里对code到id的映射进行缓存
    """
    if len(code)>3 and code[0]=='S' and (code[1]=='H' or code[1]=='Z'):
        if code[2]==':':
            code = code.replace(':','')
        b,company = shared.fromRedis(code)
        if not b:
            company = query("""select id,code,name,category from company where code='%s'"""%code)
            shared.toRedis(company,code)
    elif len(code)>3 and code[0]=='B' and code[1]=='K':
        company = query("""select id,code,name,category from company where code='%s'"""%code)
    else:
        company = query("""select id,code,name,category from company where name='%s'"""%code)
    
    if len(company)==0:
        print('数据库中没有该股票:',code)
        return (code,code,code),np.array([]),()
    if period=='d':
        if after is None:
            data = query("""select date,volume,open,high,low,close from k%s_xueqiu where id=%s"""%(str(period),company[0][0]))
        else:
            if ei is None:
                data = query("""select date,volume,open,high,low,close from k%s_xueqiu where id=%s and date>='%s'"""%(str(period),company[0][0],after))
            else:
                data = query("""select date,volume,open,high,low,close from k%s_xueqiu where id=%s and date>='%s' and date<='%s"""%(str(period),company[0][0],after,ei))
    else:
        if after is None:
            data = query("""select timestamp,volume,open,high,low,close from k%s_xueqiu where id=%s"""%(str(period),company[0][0]))
        else:
            if ei is None:
                data = query("""select timestamp,volume,open,high,low,close from k%s_xueqiu where id=%s and timestamp>='%s'"""%(str(period),company[0][0],after))
            else:
                data = query("""select timestamp,volume,open,high,low,close from k%s_xueqiu where id=%s and timestamp>='%s' and timestamp<='%s'"""%(str(period),company[0][0],after,ei))
    kdate = []
    k = []
    for i in range(len(data)):
        kdate.append((data[i][0],))
        k.append(data[i][1:])
    kline = np.array(k).reshape(-1,5)

    if expire is not None and period=='d':
        shared.numpyToRedis(kline,code+'_K',ex=expire)
        shared.toRedis(kdate,code+'_D',ex=expire)
    return company[0],kline,kdate

"""
加载资金流向数据
flow {
    0 larg, 特大 单笔>100w
    1 big,  大 20-100w
    2 mid,  中 5-20w
    3 tiny  小 <5w
}
date {
    0 - [date,]
}
"""
def loadFlow(after=None):
    if after is None:
        data = query("select date,larg,big,mid,tiny from flow order by date")
    else:
        data = query("select date,larg,big,mid,tiny from flow where date>='%s' order by date"%(after))
    flowdate = []
    flow = []
    for i in range(len(data)):
        flowdate.append((data[i][0],))
        flow.append(data[i][1:])
    flowk = np.array(flow).reshape(-1,4)
    return flowk,flowdate
"""
从共享内存加载k线数据
"""
def loadKlineCache():
    K = np.memmap('d:/temp/K',dtype='float32',mode='r')
    C = np.memmap('d:/temp/C',dtype='<U11',mode='r')
    D = np.memmap('d:/temp/D',dtype='float32',mode='r')
    Date = []
    for i in range(len(D)):
        Date.append((date.fromtimestamp(D[i]),))
    nCom = int(len(C)/7)
    Kmm = K.reshape((len(D),nCom,5))
    Kline = np.empty((len(D),nCom,5))
    Kline[:] = Kmm[:]
    Companys = C.reshape((nCom,7))
    return Companys,Kline,Date
"""
将最新的数据存入到Cache中去
"""
def updateKlineCache():
    pass
"""
创建共享内存k线数据
"""
def createKlineCache(beginDate):
    companys = query("select company_id,code,name,category,ttm,pb from company_select")
    drs = query("select id,date,volume,open,high,low,close from kd_xueqiu where date>='%s'"%(beginDate))
    """
    将数据收集成
    [id,date,feild]
    """
    ids = {}
    dates = {}
    for i in range(len(drs)):
        it = drs[i]
        idd = it[0]
        if idd not in ids:
            ids[idd] = []
            dates[idd] = []
        ids[idd].append([it[2],it[3],it[4],it[5],it[6]])
        dates[idd].append([it[1]])
    idc = {}
    for c in companys:
        idc[c[0]] = c
    #这里有3个表一个是K放置全部的Kline数据，D放置日期的timestramp，C是一个id到K中行号的映射表
    K = np.memmap('d:/temp/K',dtype='float32',mode='w+',shape=(len(ids[8828]),len(companys),5))
    C = np.memmap('d:/temp/C',dtype='<U11',mode='w+',shape=(len(companys),7))
    D = np.memmap('d:/temp/D',dtype='float32',mode='w+',shape=(len(dates[8828]),))
    for i in range(len(dates[8828])):
        D[i] = datetime.fromisoformat(str(dates[8828][i][0])).timestamp()
    print('size:',len(companys)*len(ids[8828])*5*4/1024/1024,'MB')
    i = 0
    for idd in idc:
        k = np.array(ids[idd])
        d = dates[idd]
        K[:,i,:] = alignK(dates[8828],k,d)
        C[i,0:6] = idc[idd]
        C[i,6] = i
        print(i)
        i+=1
    K.flush()
    C.flush()
    D.flush()
    del K
    del C
    del D
    print('DONE!')

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

def emaV(k,n):
    m = np.empty([len(k)])
    for i in range(len(k)):
        if i==0:
            m[0] = k[i]
        else:
            m[i] = (2*k[i]+(n-1)*m[i-1])/(n+1)
    return m
"""计算一般macd"""
def macdV(k):
    ema9 = emaV(k,9)
    ema12 = emaV(k,12)
    ema26 = emaV(k,26)
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
计算一般值的相对强弱指数RSI
计算公式来源:http://www.bary.com/doc/a/209624790300910442/
"""
def rsi(k,n=6):
    S = k[1:]-k[:-1]
    U = S
    D = np.copy(S)
    U[U<0] = 0
    D[D>0] = 0
    D = np.abs(D)
    F = emaV(U,n)+emaV(D,n)
    F[F==0] = 1
    RSI = emaV(U,n)/F
    RSI[RSI>1] = 1
    result = np.empty(len(k))
    result[0] = 50
    result[1:] = RSI*100
    return result

"""
CCI（Commodity Channel lndex）顺势指标是测量股价是否已超出常态分布范围的一个指数，
由唐纳德·R.兰伯特（DonaldLambert）所创，属于超买超卖类指标中较特殊的一种，波动于正无限大和负无限小之间。
"""
def cci():
    pass

"""
成交量能量
"""
def volumeEnergy(k,n=20):
    ve = np.zeros((len(k)))
    ma20 = ma(k,n)
    for i in range(1,len(k)):
        ve[i] = ve[i-1]+k[i]-ma20[i]
    return ve

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
    #for i in range(len(k)):
    #    if i-n+1>=0:
    #        m[i] = k[i-n+1:i+1].sum()/n
    #    else:
    #        m[i] = k[0:i+1].sum()/(i+1)
    #下面是优化方法
    if len(k)<=n:
        for i in range(len(k)):
            m[i] = k[0:i+1].sum()/(i+1)
    else:
        for i in range(n):
            m[i] = k[0:i+1].sum()/(i+1)
        dk = (k[n:]-k[:-n])/n
        for i in range(len(dk)):
            m[i+n] = m[i+n-1]+dk[i]
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
            minx = 10*k[i,2]
            mini = i
            maxx = -minx
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
将k进行合并
例如将5分钟线合并成15,30,...分钟线
该方法不进行周对齐，精确的方法使用weekK
"""
def mergeK(k,d,n):
    n = int(n)
    m = len(k)%n
    L = int(math.floor(len(k)/n))
    l = L+(1 if m!=0 else 0)
    nk = np.zeros((l,5))
    nd = []
    
    for i in range(L):
        nk[i,0] = k[i*n:i*n+n,0].sum() #volume
        nk[i,1] = k[i*n,1] #open
        nk[i,2] = k[i*n:i*n+n,2].max() #high
        nk[i,3] = k[i*n:i*n+n,3].min() #low
        nk[i,4] = k[i*n+n-1,4] #close
        nd.append(d[i*n+n-1])
    if m>0:
        nk[-1,0] = k[L*n:,0].sum() #volume
        nk[-1,1] = k[L*n,1] #open
        nk[-1,2] = k[L*n:,2].max() #high
        nk[-1,3] = k[L*n:,3].min() #low
        nk[-1,4] = k[-1,4] #close
        nd.append(d[-1])
    
    return nk,nd

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
    wdate = []
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
        wdate.append(date[i])
        i = ei+1
    if wk[-1][6]!=n-1:
        i = n-1
        ei = n-1
        wk.append([k[i:ei+1,0].sum(),k[i,1],k[i:ei+1,2].max(),k[i:ei+1,3].min(),k[ei,4],i,ei])
        wdate.append(date[i])
    return np.array(wk),wdate

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

"""
最小二乘法拟合直线
y = k*x+b
R 是拟合度
"""
def lastSequaresLine(p):
    x = np.empty((len(p),2))
    x[:,0] = np.arange(len(p))
    x[:,1] = p
    a = x.mean(axis=0)
    k = ((x[:,0]-a[0])*(x[:,1]-a[1])).sum()/((x[:,0]-a[0])**2).sum()
    b = a[1]-k*a[0]
    #拟合优度,范围0-1,越靠近1拟合越好
    R = 1-((x[:,1]-k*x[:,0]-b)**2).sum()/((x[:,1]-a[1])**2).sum()
    return [k,b,R]

"""
量价关系
[
    (bi,ei,dvolume,dprice),dvolume (-1,1) ,dvolume(-1,1)
]
"""
def volumeprices(k,d):
    volumeJ = kdj(k[:,0])[:,2]
    bi = -1
    ei = -1
    prevs = -1
    pt = []
    def add_max_volume(b,e):
        pt.append(k[b:e+1,0].argmax()+b) 
    def add_min_volume(b,e):
        pt.append(k[b:e+1,0].argmin()+b)

    for i in range(len(volumeJ)):
        J = volumeJ[i]
        if J>80:
            if prevs==1:
                add_min_volume(bi,ei)
                bi = -1
            if bi==-1:
                bi = i
            ei = i
            prevs = 0
        elif J<20:
            if prevs==0:
                add_max_volume(bi,ei)
                bi = -1
            if bi==-1:
                bi = i
            ei = i            
            prevs = 1
    if prevs==1 and bi!=-1:
        add_min_volume(bi,ei)
        add_max_volume(len(k)-1,len(k)-1) #最后一段假设趋势
    elif prevs==0 and bi!=-1:
        add_max_volume(bi,ei)
        add_min_volume(len(k)-1,len(k)-1)
    
    r = []
    for i in range(len(pt)-1):
        bi = pt[i]
        ei = pt[i+1]
        if ei>bi:
            v = lastSequaresLine(k[bi:ei+1,0]) #量
            p = lastSequaresLine(k[bi:ei+1,4]) #价
            r.append([bi,ei,v[0],p[0]])
    R = np.array(r)
    vmax = R[:,2].max()
    vmin = R[:,2].min()
    pmax = R[:,3].max()
    pmin = R[:,3].min()
    for i in range(len(R)):
        a = R[i]
        if a[2]>0:
            a[2] = a[2]/vmax
        else:
            a[2] = -a[2]/vmin
        if a[3]>0:
            a[3] = a[3]/pmax
        else:
            a[3] = -a[3]/pmin
    return R
"""
量价关系2
只要成交量放大就归为增长，直到由最高开始下落
"""
def volumeprices2(k,d):
    pass
"""
因为一天中不同时段的成交量是个‘碗’型，使用这样的成交量计算出的energy没有参考意义
这里对成交量进行修正使得不同时段的成交量看上去是一条‘直线’
方法：使用n天的‘碗’型做平均作为校正的依据
返回校正过的成交量，不具有绝对意义经有相对意义的量
period = 1,5,15,...
"""
def correctionVolume(k,d,period,n=10):
    periodN = {
        1:16*3*5,
        5:16*3,
        15:16,
        30:8,
        60:4,
        120:2
    }
    N = periodN[period]
    if len(k)%N==0:
        complete = 0
    else:
        complete = N-len(k)%N

    volume = np.zeros(len(k)+complete)
    volume[:len(k)] = k[:,0]
    
    volumed = volume.reshape(-1,N)
    mad = np.empty((len(volumed),N))
    for i in range(N):
        mad[:,i] = ma(volumed[:,i],n)
    for i in range(len(volumed)):
        avg = mad[i,:].mean()
        for j in range(N):
            volumed[i,j] *= avg/mad[i,j]
    return volume[:len(k)],mad

"""
计算支撑位和压力位置 ,还在测试
"""
def spp(k,n=60):
    ei = len(k)-1
    bi = ei-n
    if bi<0:
        bi = 0
    pp = [] #压力位置
    sp = [] #支持文章
    for i in range(bi,ei):
        if i-1>=bi and i+1<ei:
            if k[i,2]>k[i+1,2] and k[i,2]>k[i-1,2]:
                pp.append((i,k[i,2]))
            if k[i,3]<k[i+1,3] and k[i,3]<k[i-1,3]:
                sp.append((i,k[i,3]))
    return sp,pp