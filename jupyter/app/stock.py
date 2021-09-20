import MySQLdb
import numpy as np
import math
import time
from datetime import date,datetime,timedelta
from . import shared
from . import config
from . import mylog

def isTransTime(t=None):
    if t is None:
        t = datetime.today()
    #包括集合竞价
    return ((t.hour==9 and t.minute>=15) or t.hour==10 or (t.hour==11 and t.minute<30) or (t.hour>=13 and t.hour<15)) or (t.hour==15 and t.minute==0) and t.weekday()>=0 and t.weekday()<5

#判断今天是不是可以交易
def isTransDay(t=None):
    if t is None:
        t = datetime.today()
    if t.weekday()>=0 and t.weekday()<5:
        return True
    else:
        return False

def dateString(t):
    return '%d-%02d-%02d'%(t.year,t.month,t.day)
def timeString(t):
    return '%d-%02d-%02d %02d:%02d:%02d'%(t.year,t.month,t.day,t.hour,t.minute,t.second)
def timeString2(t):
    return '%02d:%02d:%02d'%(t.hour,t.minute,t.second)

def date2time(d):
    return datetime(year=d.year,month=d.month,day=d.day)
    
gdb = None

def escape_string(d):
    return MySQLdb.escape_string(d)
    
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
    try:
        if gdb is None:
            opendb()
        gdb.query(s)
        r = gdb.store_result()
    except Exception as e:
        mylog.printe(e)
        print(s)
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
        mylog.printe(e)
        gdb.rollback()
        print(s)
"""
加载股票数据
返回的第一个数据
company (
    0 - id,
    1 - code,
    2 - name,
    3 - category,
    4 - done,
    5 - kbegin,
    6 - kend
    ...)
kline [(
    0 - volume,
    1 - open,
    2 - high,
    3 - low,
    4 - close
    ),...]
kdate [(date,),...]
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

    suffix = 'xueqiu'
    """
    这里对code到id的映射进行缓存
    """
    if len(code)>3 and code[0]=='S' and (code[1]=='H' or code[1]=='Z'):
        if code[2]==':':
            code = code.replace(':','')
        b,company = shared.fromRedis(code)
        if not b or len(company)==0:
            company = query("""select id,code,name,category from company where code='%s'"""%code)
            shared.toRedis(company,code,ex=24*3600)
    elif len(code)>3 and code[0]=='B' and code[1]=='K':
        em = query("""select * from flow_em_category where code='%s'"""%code) #代码重复优先em
        if len(em)>0:
            company = [(em[0][5],em[0][2],em[0][1],'EM')]
            suffix = 'em'
        else:
            company = query("""select id,code,name,category from company where code='%s'"""%code)
    else:
        while True:
            #code没有SH和SZ则尝试两种前缀
            if code[0].isnumeric():
                b,company = shared.fromRedis('SZ%s'%code)
                if b:
                    break
                b,company = shared.fromRedis('SH%s'%code)
                if b:
                    break
                company = query("""select id,code,name,category from company where code='SZ%s'"""%code)
                if len(company)>0:
                    break
                company = query("""select id,code,name,category from company where code='SH%s'"""%code)
                if len(company)>0:
                    break
            else:
                #尝试名称
                company = query("""select id,code,name,category from company where name='%s'"""%code)
            break
    
    
    if len(company)==0:
        #加载板块k,code==板块名称
        if period=='d':
            print('数据库中没有该股票:',code)
            return (code,code,code),np.array([]),()
        company = query("""select id,code,name,name,name from category where name='%s'"""%code)
        if len(company)==0:
            print('数据库中没有该板块:',code)
            return (code,code,code),np.array([]),()
        suffix = 'category'
        
    db = "k%s_%s"%(str(period),suffix)
    if period=='d':
        if after is None:
            data = query("""select date,volume,open,high,low,close from %s where id=%s"""%(db,company[0][0]))
        else:
            if ei is None:
                data = query("""select date,volume,open,high,low,close from %s where id=%s and date>='%s'"""%(db,company[0][0],after))
            else:
                data = query("""select date,volume,open,high,low,close from %s where id=%s and date>='%s' and date<='%s'"""%(db,company[0][0],after,ei))
    else:
        if after is None:
            data = query("""select timestamp,volume,open,high,low,close from %s where id=%s"""%(db,company[0][0]))
        else:
            if ei is None:
                data = query("""select timestamp,volume,open,high,low,close from %s where id=%s and timestamp>='%s'"""%(db,company[0][0],after))
            else:
                data = query("""select timestamp,volume,open,high,low,close from %s where id=%s and timestamp>='%s' and timestamp<='%s'"""%(db,company[0][0],after,ei))
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
def loadFlow(after=None,dd=None,ei=None):
    if after is None:
        if dd is None:
            data = query("select date,larg,big,mid,tiny from flow order by date")
        else:
            data = query("select date,larg,big,mid,tiny from flow where date>='%s' and date<'%s' order by date"%(dateString(dd),dateString(dd+timedelta(days=1))))
    else:
        if ei is None:
            data = query("select date,larg,big,mid,tiny from flow where date>='%s' order by date"%(after))
        else:
            data = query("select date,larg,big,mid,tiny from flow where date>='%s' and date<='%s' order by date"%(after,ei))
    flowdate = []
    flow = []
    for i in range(len(data)):
        flowdate.append((data[i][0],))
        flow.append(data[i][1:])
    flowk = np.array(flow).reshape(-1,4)
    return flowk,flowdate
 
def loademFlow(code,after=None,dd=None,ei=None):
    qs = query("select id from flow_em_category where code='%s' and watch!=-1"%(code))
    if len(qs)==1:
        id = int(qs[0][0])
        if after is None:
            if dd is None:
                data = query("select timestamp,larg,big,mid,tiny from flow_em where id=%d order by timestamp"%(id))
            else:
                data = query("select timestamp,larg,big,mid,tiny from flow_em where id=%d and timestamp>='%s' and timestamp<'%s' order by timestamp"%(id,dateString(dd),dateString(dd+timedelta(days=1))))
        else:
            if ei is None:
                data = query("select timestamp,larg,big,mid,tiny from flow_em where id=%d and timestamp>='%s' order by timestamp"%(id,after))
            else:
                data = query("select timestamp,larg,big,mid,tiny from flow_em where id=%d and timestamp>='%s' and timestamp<='%s' order by timestamp"%(id,after,ei))
        flowdate = []
        flow = []
        for i in range(len(data)):
            flowdate.append((data[i][0],))
            flow.append(data[i][1:])
        flowk = np.array(flow).reshape(-1,4)
        return True,flowk,flowdate
    else:
        return False,None,None
"""
从共享内存加载k线数据
"""
def loadKlineMM():
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
和loadKline一样只是增加redis缓存
缓存数据(c,k,d)
"""
g_kd = {}
def loadKlineCache(code,period,bi):
    global g_kd
    name = '%s_%s.kcach'%(code,period)
    if period=='d':
        tbi = date.fromisoformat(bi)
    else:
        tbi = datetime.fromisoformat(bi)    
    if name in g_kd and (g_kd[name][2][0][0]-tbi<=timedelta(days=1) or g_kd[name][3]):
        return g_kd[name][:3]
    b,z = shared.fromRedis(name)
    if b and z[1] is not None and z[2] is not None:
        (c,k,d) = z

        if d[0][0]>tbi:
            nc,nk,nd = loadKline(code,period,after=bi,ei= dateString(d[0][0]) if period=='d' else timeString(d[0][0]))
            #加载新数据，组合
            if nd[-1][0]==d[0][0]: #重叠一个
                k = np.vstack((nk[:-1],k))
                d = nd[:-1] + d
            else:
                k = np.vstack((nk,k))
                d = nd + d
        else: #直接返回数据，数据量可能更多
            g_kd[name] = (c,k,d)
            return c,k,d
    else:
        c,k,d = loadKline(code,period,after=bi)
    
    shared.toRedis((c,k,d),name,ex=3600*12) #存储12小时
    isall = (d[0][0]-tbi>timedelta(days=5)) #表示数据已经全部加载了
    g_kd[name] = (c,k,d,isall)
    return c,k,d

"""
将最新的数据存入到Cache中去
"""
def updateKlineCache():
    pass
"""
创建共享内存k线数据
"""
def createKlineMM(beginDate):
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
    m[0] = k[0,4]
    for i in range(1,len(k)):
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
    #emA = np.empty([len(k),3])
    #emA[:,0] = ema9
    #emA[:,1] = ema12
    #emA[:,2] = ema26
    DIF = ema12-ema26
    MACD = 224.*ema9/51.-16.*ema12/3.+16.*ema26/17.
    DEA = DIF-0.5*MACD
    return MACD,DIF,DEA

def emaV(k,n):
    m = np.empty([len(k)])
    m[0] = k[0]
    for i in range(1,len(k)):
        m[i] = (2*k[i]+(n-1)*m[i-1])/(n+1)
    return m
"""计算一般macd"""
def macdV(k):
    ema9 = emaV(k,9)
    ema12 = emaV(k,12)
    ema26 = emaV(k,26)
    #emA = np.empty([len(k),3])
    #emA[:,0] = ema9
    #emA[:,1] = ema12
    #emA[:,2] = ema26
    DIF = ema12-ema26
    MACD = 224.*ema9/51.-16.*ema12/3.+16.*ema26/17.
    DEA = DIF-.5*MACD    
    return MACD,DIF,DEA
"""对矩阵进行批量计算"""    
def emaMatrix(k,n):
    m = np.empty(k.shape)
    m[:,0] = k[:,0]
    for i in range(1,k.shape[1]):
        m[:,i] = (2*k[:,i]+(n-1)*m[:,i-1])/(n+1)
    return m
def macdMatrix(k):
    ema9 = emaMatrix(k,9)
    ema12 = emaMatrix(k,12)
    ema26 = emaMatrix(k,26)
    DIF = ema12-ema26
    MACD = 224.*ema9/51.-16.*ema12/3.+16.*ema26/17.
    DEA = DIF-0.5*MACD
    return MACD,DIF,DEA    
def maMatrix(k,n):
    m = np.empty(k.shape)
    if len(k)<=n:
        for i in range(k.shape[1]):
            m[:,i] = k[:,0:i+1].sum(axis=1)/(i+1)
    else:
        for i in range(n):
            m[:,i] = k[:,0:i+1].sum(axis=1)/(i+1)
        dk = (k[:,n:]-k[:,:-n])/n
        for i in range(dk.shape[1]):
            m[:,i+n] = m[:,i+n-1]+dk[:,i]
    return m
def bollMatrix(k,n=20):
    MB = maMatrix(k,n)
    """计算标准差"""
    MD = np.empty(k.shape)
    for i in range(k.shape[1]):
        MA = MB[:,i]
        if i-n+1>=0:
            #FIXBUG
            a = np.sqrt(((k[:,i-n+1:i+1]-MA)**2).sum(axis=1)/n)
            MD[:,i] = a
        else:
            a = np.sqrt(((k[:,0:i+1]-MA)**2).sum(axis=1)/(i+1))
            MD[:,i] = a
    return MB,MB-2*MD,MB+2*MD
def slopeRatesMatrix(m):
    r = np.empty(m.shape)
    r[:,0] = 0
    sz = m[:,0]==0
    m[sz,:] = 0.0000001
    Len = m.shape[1]
    r[:,1:Len] = (m[:,1:Len]-m[:,0:Len-1])/m[:,0:Len-1]
    return r

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
def slopeRates(m):
    r = np.empty(len(m))
    r[0] = 0
    sz = m[:]==0
    m[sz] = 0.0000001
    r[1:len(m)] = (m[1:len(m)]-m[0:len(m)-1])/m[0:len(m)-1]
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

def date2datetime(d):
    ts = []
    for v in d:
        t = v[0]
        ts.append((datetime(year=t.year,month=t.month,day=t.day),))
    return ts
"""
将k,d映射到新的时序周期中
例如：k,d是日线数据,newd是60分钟时序
"""
def periodExpand(k,d,newd):
    off = 1
    if type(d[0][0])==date:
        d = date2datetime(d)
    if len(k.shape)==1:
        newk = np.zeros((len(newd)))
    else:
        newk = np.zeros((len(newd),k.shape[1]))  

    for i in range(len(newd)):
        t = newd[i][0]
        b = False
        for j in range(off,len(d)):
            if d[j][0]>t:
                newk[i] = k[j-1]
                off = j
                b = True
                break
        if not b and off==len(d)-1:
            newk[i] = k[-1]
            
    return newk
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

"""
一堆股票的指数计算方法
输入的是k,输出指数k
"""
def index(ks):
    pass

"""
沿着v从后到前发现n个正极值点
"""
def extremePoint(m,n=2):
    r = []
    s = []
    v = m
    last = -1
    for i in range(len(v)-2,0,-1):
        if v[i+1]<v[i] and v[i]>v[i-1]:
            a = (i,1,v[i])
        elif v[i+1]>v[i] and v[i]<v[i-1]:
            a = (i,-1,v[i])
        else:
            continue
        if last>0 and last-i>n: #将间距小于n的放在一起
            r.append(s)
            s = [a]
        else:
            s.append(a)
        last = i
    if len(s)>0:
        r.append(s)
    """
    如果极值太过靠近，需要对其进行合并
    """
    R = []
    for s in r:
        if len(s)==1:
            R.append(s[0])
        elif s[-1][1]*s[0][1]>0: #如果首尾都是顶或者底
            if s[0][1]>0: #如果这一组首位都是顶部，取中间最大的
                R.append(max(s,key=lambda it:it[2]))
            else: #取最小的
                R.append(min(s,key=lambda it:it[2]))
        else: #如果收尾不同反向就忽略掉
            pass

    return R

"""
macd背离侦测
返回[(顶或者底背离1或者-1,bi,ei),...]
"""
def macdDeviate(v,m=None,n=2):
    if m is None:
        m,_,_ = macdV(v)
    eps = extremePoint(m,n=n)
    R = []
    for i in range(len(eps)-2):
        ep0 = eps[i]
        ep1 = eps[i+1]
        ep2 = eps[i+2]
        if ep0[1]>0 and ep2[1]>0 and ep1[1]<0 and ep0[2]>0 and ep1[2]>0 and ep2[2]>0 and ep0[2]<ep2[2] and v[ep0[0]]>v[ep2[0]]: #顶背离
            R.append((1,ep2[0],ep0[0]))
        elif ep0[1]<0 and ep2[1]<0 and ep1[1]>0 and ep0[2]<0 and ep1[2]<0 and ep2[2]<0 and ep0[2]>ep2[2] and v[ep0[0]]<v[ep2[0]]: #低背离
            R.append((-1,ep2[0],ep0[0]))
    return R

"""
返回全部股票的总市值
通过成交量除以还手率
"""
def totalVolume(date=None):
    if date is None:
        dd = query("""select date from kd_xueqiu where id=8828 order by date desc limit 1""")
        #做个一天的缓存
        date = dateString(dd[0][0])
    n = "tv%s"%date
    b,V = shared.numpyFromRedis(n)
    if b:
        return V
    v = query("""select id,volume,turnoverrate from kd_xueqiu where date='%s'"""%(date))
    V = np.array(v).reshape(-1,3)
    V[V[:,2]==0,2] = 1
    V[:,1] = V[:,1]/V[:,2]
    shared.numpyToRedis(V[:,:2],n,ex=24*3600)
    return V[:,:2]

"""
K线缺口
输入标准k数据
返回缺口数据[(bi,ei,low,high,dp),...]
缺口开始位置bi,缺口结束位置ei,缺口大小high-low
dp是1跳空高开缺口，-1跳空低开缺口
"""
def gap(k):
    R = []
    for i in range(len(k)-1):
        K1 = k[i]
        K2 = k[i+1]
        if K1[2]<K2[3] or K1[3]>K2[2]: #存在缺口
            bi = i
            ei = len(k)-1
            if K1[2]<K2[3]:
                low = K1[2]
                high = K2[3]
                dp = 1
            else:
                low = K2[2]
                high = K1[3]
                dp = -1
            for j in range(i+1,len(k)): #搜索封闭点
                K = k[j]
                if K[2]<high and K[2]>low:
                    low = K[2]
                elif K[3]<high and K[3]>low:
                    high = K[3]
                elif K[2]>=high and K[3]<=low: #封闭
                    low = high+1 #使得high<low
                    break
                if low>=high: #封闭了
                    break
            if high>low:
                R.append((bi,ei,low,high,dp))
    return R

"""
计算一组股票的指数 
"""

"""
计算均线对股价的支撑
n支撑均线
m也是均线数字，且m>n,仅仅当m均线的斜率向上的时候才满足条件
b是一个小级别均线
返回:一个索引位置数组，将可能的支撑位置标记出来
[(高点，低点，支撑点),...]
"""
def calcHoldup(k,date,n,m=None,b=3):
    man = maK(k,n)
    manS = slopeRates(man)
    manb = maK(k,b)
    manbS = slopeRates(manb)
    mam = None
    mamS = None
    result = []
    if m is not None and m>n:
        mam = maK(k,m)
        mamS = slopeRates(mam)
    dif = manb-man
    lastHighD = 0 #最近股价偏离均线的最高点
    lastHighI = 0 #最高点位置
    lastLowD = 1e10 #最近的股价最靠近均线的低点
    lastLowI = 0 #最低点位置
    insertLastHighI = 0
    insertLastLowI = 0
    for i in range(3,len(k)):
        """判断是否足够靠近支撑均线
        1.如果过往b个k线最低点穿过，如果穿过和最近在均线上的最高点偏离值比较，要小于它的1/2
        2.如果没有穿过，判断是否足够接近均线。小于最近在均线上的最高偏离的1/4
        """
        if dif[i]>0 and dif[i]>lastHighD:
            lastHighD = dif[i]
            lastHighI = i
            lastLowD = 1e10
            lastLowI = 0
        elif dif[i]<lastLowD:
            lastLowD = dif[i]
            lastLowI = i
        if lastHighD/5>lastLowD and lastLowD!=1e10 and lastLowI>lastHighI and i>lastLowI and lastLowI-lastHighI>n/6\
            and (lastHighD-lastLowD)/16<(dif[i]-lastLowD):#((lastLowD<0 and manb[i]>man[i]) or (lastLowD>0 and (lastHighD-lastLowD)/12<(dif[i]-lastLowD))):
            if mam is not None:
                if mamS[i]>0 and manS[lastLowI]>0 and manbS[i]>0: #反弹最低点的时斜率要向上
                    if lastHighI!=insertLastHighI or lastLowI!=insertLastLowI: #同一个高点和低点确保只会插入一次
                        insertLastHighI = lastHighI
                        insertLastLowI = lastLowI
                        result.append((lastHighI,lastLowI,i))
            elif manS[lastLowI]>0 and manbS[i]>0:
                if lastHighI!=insertLastHighI or lastLowI!=insertLastLowI:
                    insertLastHighI = lastHighI
                    insertLastLowI = lastLowI
                    result.append((lastHighI,lastLowI,i))
        #print(date[lastHighI][0],date[lastLowI][0],lastHighD-lastLowD,dif[i]-lastLowD,lastHighD,lastLowD,dif[i])
        if (lastLowD!=1e10 and ((lastHighD-lastLowD)*2/3<(dif[i]-lastLowD)) or (manS[i]<0 and  manS[i-1]<0 and  manS[i-2]<0)):#重新开始
            lastHighD = 0
            lastHighI = 0
            lastLowD = 1e10
            lastLowI = 0
            
    return result

"""
从尾部向前搜索中枢
方法:通过加大搜索范围来
返回b,(通道长度，上限，下限)
"""
def bollwayex(k,n=16,jcn=3):
    for i in range(5*n,0,-n):
        b,a = bollway(k,i,jcn)
        if b:
            return b,a
    return False,(0,0,0,0)
"""
从尾部向前搜索中枢
方法:先确定一个高点范围，和低点范围，然后如果k在高点和低点之间交替超过2次
返回b,(通道长度，上限，下限)
"""
def bollway(k,n=16,jcn=3):
    if len(k)>n:
        argv = k[-n-1:-1].mean()
        real_maxv = np.amax(k[-n-1:-1])
        real_minv = np.amin(k[-n-1:-1])
        maxv = real_maxv
        minv = real_minv
        if maxv-argv>argv-minv: #取离平均数较近的作为通道宽度的一半
            maxv = 2*argv-minv
        else:
            minv = 2*argv-maxv
        delta = (maxv-minv)*0.191 #黄金分割
        upmax = maxv+delta
        upmin = maxv-delta
        downmax = minv+delta
        downmin = minv-delta
        f = []
        for i in range(-1,-len(k),-1):
            p = k[i]
            if p<upmax and p>upmin:
                f.append((i,1))
            elif p<downmax and p>downmin:
                f.append((i,-1))
            elif p>upmax or p<downmin:
                break
        N = -i-1 #通道长度
        if N>=n:
            zfc = 0
            zfn = 0 #交替次数
            for it in f:
                if it[1]!=zfc:
                    zfn+=1
                    zfc = it[1]
            if minv==0:
                return False,(0,0,0,0)
            r = (maxv-minv)/minv
            return zfn>jcn and r>0.016 and r<0.08,(N,real_minv,real_maxv,zfn)
    return False,(0,0,0,0)

"""
对通道算法进行优化
def bollway2(k,d,n=48*3,jcn=3):
    for i in range(-len(k)+1,1,-1):
"""

#对通道做延申处理,幅度做收缩处理
def extway(k,i,n,mink,maxk):
    bi = i-n
    #向两侧扩展
    for bi in range(i-n,0,-1):
        if k[bi]>maxk or k[bi]<mink:
            break
    ei = i
    for ei in range(i,0,1):
        if k[ei]>maxk or k[ei]<mink:
            break
    #向内部压缩，确保有一定比率的k向在通道外面
    dk = (maxk-mink)/20
    up = maxk
    for j in range(1,10):
        up = maxk-dk*j
        if np.count_nonzero(k[bi:ei]>up)/(ei-bi)>0.16:
            break
    down = mink
    for j in range(1,10):
        down = mink+dk*j
        if np.count_nonzero(k[bi:ei]<down)/(ei-bi)>0.16:
            break            
    return bi,ei,down,up
"""
将biei映射到d日期的索引
"""
def get_date_i(d,b,e):
    bi = 0
    ei = 0
    if type(d[0][0])==datetime:
        for i in range(len(d)):
            t = d[i][0]
            if bi==0 and t>=b:
                bi = i
            if ei==0 and t>=e:
                ei = i
                break
    else:
        for i in range(len(d)):
            t = d[i][0]
            t = datetime(year=t.year,month=t.month,day=t.day)
            if bi==0 and t>=b:
                bi = i
            if ei==0 and t>=e:
                ei = i
                break
    return bi,ei    
"""
分析股价与boll通道的关系
"""
#提示，1 早盘 2放量 3流入 4 站上5日均线或者某一级别boll突破

"""
对分时线进行分析
返回[0开盘，1上午最低，2上午最高，3收盘，4将上午时间轴视为0-1则最低点值,5最高点值]
"""
def pkfx(k,d):
    if len(d)==0:
        return None    
    openv = 0
    low = 1e9
    high = 0
    t = d[0]
    tbi = datetime(year=t.year,month=t.month,day=t.day,hour=9,minute=30)
    tei = datetime(year=t.year,month=t.month,day=t.day,hour=11,minute=30)
    lowt = tbi
    hight = tbi
    for i in range(len(k)):
        if openv==0 and d[i]>=tbi:
            openv = k
        if d[i]>=tbi and d[i]<=tei:
            if k[i]<low:
                low = k[i]
                lowt = d[i]
            if k[i]>high:
                high = k[i]
                hight = d[i]
        if d[i]>=tei:
            break
    
    return (openv,low,high,k[-1],(lowt-tbi)/(tei-tbi),(hight-tbi)/(tei-tbi))

"""
对数据平滑度进行量化，数据如果是单项递增的返回1，数据越是锯齿比较多越是小，最小为0
"""
def smooth(v):
    n = 0
    for i in range(len(v)-2):
        if (v[i+1]>=v[i] and v[i+2]>=v[i+1]) or (v[i+1]<=v[i] and v[i+2]<=v[i+1]):
            n+=1
    r = n/len(v)
    r = (r-0.45)/(0.9-0.45)

    if r<0:
        r = 0
    if r>1:
        r = 1
    return r

"""
判断流是一个圆弧底
1.圆弧最低点在中间
2.大部分小于0
"""
def isArcBottom(v):
    mini = np.argmin(v)
    r = mini/len(v)
    le = len(v[v<0])
    N = len(v)
    leN = le/N
    return abs(r-0.5)<0.2 and leN>0.9 and v[0]>v[mini]/2

"""
区间x0-x1 和 x2-x3覆盖率是多少
完全不覆盖<0,完全覆盖返回1,正好不覆盖返回0
"""
def overlay(x0,x1,x2,x3):
    xx0 = min(x0,x1)
    xx1 = max(x0,x1)
    xx2 = min(x2,x3)
    xx3 = max(x2,x3)
    addw = xx1-xx0+xx3-xx2 #收尾相连的长度
    maxw = max(xx1-xx0,xx3-xx2)
    w = (max(xx1,xx3)-min(xx0,xx2)) #两端头尾的长度
    r = (w-addw)/(maxw-addw)
    return r

"""
对通道进行过滤
1.净量多的周期
2.多周期必须最大重叠
"""
def isStrongBollway(bolls):
    if len(bolls)<2: #必须有2个
        return False
    #确保时间部分尽量重叠
    max_dt = timedelta(seconds=1)
    bi,ei = None,None
    max_width = 0
    maxp = 0
    minp = 1e9
    for bo in bolls:
        if bo[8]-bo[7]>max_dt:
            max_dt = bo[8]-bo[7]
            bi = bo[7]
            ei = bo[8]
        if bo[6]-bo[5]>max_width:
            max_width = bo[6]-bo[5]
            maxp = bo[6]
            minp = bo[5]
    if bi is None:
        return False
    if ei-bi<timedelta(days=5): #最长通道必须大于5天
        return False
    for bo in bolls:
        if overlay(bo[7].timestamp(),bo[8].timestamp(),bi.timestamp(),ei.timestamp())<0.618:
            return False
    #确保在涨幅上尽量重叠
    for bo in bolls:
        if overlay(bo[5],bo[6],minp,maxp)<0.618:
            return False
    return True

def getBollwayRange(bolls):
    """
    通道的上部和下部
    """
    up = 0
    down = 0
    if len(bolls)>0:
        for bo in bolls:
            up += bo[6]
            down += bo[5]
        return down/len(bolls),up/len(bolls)
    else:
        return (0,0)

def timethis(func):
    """
    函数测速装饰器
    """
    def wraper(*args,**kwargs):
        start = time.time()
        result = func(*args,**kwargs)
        print(func.__name__,time.time()-start)
        return result
    return wraper

def completion(k):
    """
    如果数据是0就使用它后面的非0数据补全
    """
    for i in range(-2,-len(k),-1):
        if k[i]==0:
            k[i] = k[i+1]

def isHoldStock(code,name='hold'):
    """
    判断是否持有该股票
    """
    b,ls = shared.fromRedis(name)
    return b and code in ls
def holdStock(code,b,name='hold'):
    """
    b True持有，b False不持有
    """
    try:
        b1,ls = shared.fromRedis(name)
        if b:
            if not b1:
                ls = []
            if code not in ls:
                ls.append(code)
        else:
            if b1:
                ls.remove(code)
        shared.toRedis(ls,name)
    except:
        pass
def getHoldStocks(name='hold'):
    """
    返回持有的代码列表
    """
    b,ls = shared.fromRedis(name)
    return ls if b else []
