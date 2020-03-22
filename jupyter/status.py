"""
对所有股票进行计算
计算器日macd，周macd，日能量，周能量，日成交量kdJ,周成交量kdJ
算法是增量优化的，每次运行仅仅计算增加的部分
"""
import numpy as np
import stock
import xueqiu
import kline
from IPython.display import display,Markdown
import ipywidgets as widgets
from ipywidgets import Layout, Button, Box
from datetime import date,datetime,timedelta
import matplotlib.pyplot as plt
import math
import shared
import random
import threading
import time
import copy
import mylog
from matplotlib.ticker import Formatter

mylog.init('./log/status.log',name='status')
class MyFormatterRT(Formatter):
    def __init__(self, dates,fmt='%d %h:%M:%s'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0 or math.ceil(x)!=math.floor(x):
            return ''

        t = self.dates[ind][0]
        return '%d %02d:%02d:%02d'%(t.day,t.hour,t.minute,t.second)

PROD = 40

def popularCategory():
    #    ls = ['半导体','光学光电子','计算机应用','电子制造','生物制品','通信设备','医药商业','饮料制造','多元金融',
#          '证券','互联网传媒','化学制药','医疗器械','文化传媒','元件','高低压设备','环保工程及服务','地面兵装','专业工程',
#          '其他电子','营销传播','视听器材','电气自动化设备','医疗服务','专用设备','计算机设备','电源设备','贸易']
    ls = ['白色家电','半导体','光学光电子','计算机应用','电子制造','生物制品','通信设备','医药商业','饮料制造','多元金融',
          '证券','互联网传媒','化学制药','医疗器械','文化传媒','元件','高低压设备','环保工程及服务','地面兵装','专业工程','采掘服务','化学制品','化学纤维',
          '其他电子','营销传播','视听器材','电气自动化设备','医疗服务','专用设备','计算机设备','电源设备','贸易','林业','畜禽养殖','农产品加工','种植业']
    return ls
def isPopularCategory(name):
    return name in popularCategory()

def allCategoryGlobal():
    ls = stock.query("select name from category")
    r = []
    for l in ls:
        r.append(l[0])
    return r
_all_category = allCategoryGlobal()    
def allCategory():
    global _all_category
    return _all_category

#见数据插入到company_status表
def insert_company_status(k,vma20,energy,volumeJ,boll,bollw,idd):
    if len(k)>0:
        qs = ""
        for i in range(len(k)):
            #id , date , close , volume , volumema20 , macd , energy , voluemJ , bollup , bollmid, bolldn , bollw
            try:
                macd = 0 if k[i][3] is None else k[i][3]
                if i!=len(k)-1:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f,%f,%f,%f,%f),"""%(k[i][0],stock.dateString(idd[i]),k[i][2],k[i][1],vma20[i],macd,energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i])
                else:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f,%f,%f,%f,%f)"""%(k[i][0],stock.dateString(idd[i]),k[i][2],k[i][1],vma20[i],macd,energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i])
            except Exception as e:
                print(e)
                print(k[i])
                print(idd[i])
        stock.execute("insert ignore into company_status values %s"%(qs))

#bi是更新点-1插入全部
def update_company_status_week(cid,k,macd,vma20,energy,volumeJ,boll,bollw,idd,bi):
    if len(k)>0:
        #下面更新接头部分的值
        i = bi
        if bi>0:
            qs = "update company_status_week set close=%f,volume=%f,macd=%f,volumema20=%f,energy=%f,volumeJ=%f,bollup=%f,bollmid=%f,bolldn=%f,bollw=%f where id=%d and date='%s'"%\
            (k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i],cid,stock.dateString(idd[i][0]))
            stock.execute(qs)

        #下面是插入新的值
        if bi+1<len(k):
            qs = ""
            for i in range(bi+1,len(k)):
                #id , date , close , volume , macd , volumema20 , energy , voluemJ, bollup , bollmid, bolldn , bollw
                #k0 volume,1 open,2 high,3 low,4 close
                if i!=len(k)-1:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f,%f,%f,%f,%f),"""%(cid,stock.dateString(idd[i][0]),k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i])
                else:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f,%f,%f,%f,%f)"""%(cid,stock.dateString(idd[i][0]),k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i])
            stock.execute("insert ignore into company_status_week values %s"%(qs))

#依据完整数据更新
def update_company_status_all_data(idk,idd):
    k = np.array(idk)
    #k= [0 id,1 volume,2 close,3 macd ]
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]
    boll = stock.boll(k[:,2])
    bollw = stock.bollWidth(boll)
    insert_company_status(k,vma20,energy,volumeJ,boll,bollw,idd)

#依据增量数据更新
def update_company_status_delta_data(idk,idd):
    k = np.array(idk)
    #k= [0 id,1 volume,2 close,3 macd ]
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]
    boll = stock.boll(k[:,2])
    bollw = stock.bollWidth(boll)
    if len(k)>PROD:
        insert_company_status(k[PROD+1:],vma20[PROD+1:],energy[PROD+1:],volumeJ[PROD+1:],boll[PROD+1:],bollw[PROD+1:],idd[PROD+1:])
    else:
        insert_company_status(k,vma20,energy,volumeJ,boll,bollw,idd)

#可以从一个起点日期使用增量进行更新，或者更新全部数据
def update_status_begin(beginday,isall,progress):
    if isall:
        rs = stock.query("""select id,date,volume,close,macd from kd_xueqiu where date>'%s'"""%(beginday))
        progress(30)
    else:
        #需要提前20个交易日的数据
        lastdays = stock.query("select date from kd_xueqiu where id=8828 and date>'2019-11-01' order by date desc")
        progress(30)
        #从beginday前面在增加20个交易日
        for i in range(len(lastdays)):
            if lastdays[i][0] == beginday:
                lastday = lastdays[i+PROD][0]
                break

        rs = stock.query("""select id,date,volume,close,macd from kd_xueqiu where date>='%s'"""%(lastday))
    idk = {}
    idd = {}
    for i in range(len(rs)):
        d = rs[i]
        key = d[0]
        if key not in idk:
            idk[key] = []
            idd[key] = []
        #0 id,1 volume,2 close,3 macd
        idk[key].append([rs[i][0],rs[i][2],rs[i][3],rs[i][4]])
        idd[key].append(rs[i][1])
    progress(40)
    count = 0
    if isall:
        for key in idk:
            update_company_status_all_data(idk[key],idd[key])
            count+=1
            progress(math.floor(60*count/len(idk))+40)
    else:
        for key in idk:
            update_company_status_delta_data(idk[key],idd[key])
            count+=1
            progress(math.floor(60*count/len(idk))+40)

#更新company_status表
def update_status(progress):
    lastday = stock.query('select date from company_status where id=8828 order by date desc limit 1')
    progress(10)
    if len(lastday)==1:
        kdd = stock.query('select date from kd_xueqiu where id=8828 order by date desc limit 1')
        progress(20)
        if lastday[0][0] != kdd[0][0]:
            shared.delKey('company_status_last50') #清除redis中的缓存数据
            shared.delKey('company_status_date50') #清除redis中的缓存数据
            update_status_begin(lastday[0][0],False,progress)
    else:
        update_status_begin('2015-1-2',True,progress)
    stock.closedb()
    progress(100)

#更新company_status_week表
def update_status_week(progress):
    lastupdate = stock.query('select status_week_update from data')
    progress(5)
    lastday = stock.query('select date from kd_xueqiu where id=8828 order by date desc limit 1')
    progress(10)
    if len(lastupdate)>0 and lastupdate[0][0] == lastday[0][0]:
        progress(100)
        return #已经更新了
    
    shared.delKey('company_status_week_last50') #清除redis中的缓存数据
    shared.delKey('company_status_week_date50') #清除redis中的缓存数据
    alldate = stock.query("select date from company_status_week where id=8828 order by date desc")
    progress(20)
    if len(alldate)==0:
        drs = stock.query("select id,date,volume,close from kd_xueqiu where date>'2010-1-2'")
        progress(50)
        wrs = [] #没有数据
    else:
        #从日线数据中取出未更新部分数据
        drs = stock.query("select id,date,volume,close from kd_xueqiu where date>='%s'"%(alldate[1][0])) #最近两个星期的日线数据
        progress(40)
        #从周状态中取出一部分历史数据
        wrs = stock.query("select id,date,volume,close from company_status_week where date>='%s'"%(alldate[PROD+1][0])) #最近40天的周线数据
        progress(50)
    
    #按个股进行重新存储idk[id] = 该id的k线, idd[id] = 该id的日期数组
    idk = {} #
    idd = {}
    for i in range(len(drs)):
        key = drs[i][0]
        if key not in idk:
            idk[key] = []
            idd[key] = []
        #volume,open,high,low,close
        idk[key].append([drs[i][2],0,0,0,drs[i][3]])
        idd[key].append([drs[i][1]])
    progress(60)
    wdk = {} #
    wdd = {}
    for i in range(len(wrs)):
        key = wrs[i][0]
        if key not in wdk:
            wdk[key] = []
            wdd[key] = []
        #id,volume,close
        wdk[key].append([key,wrs[i][2],wrs[i][3]])
        wdd[key].append([wrs[i][1]])
    progress(70)
    for key in idk:
        k = idk[key]
        d = idd[key]

        if key not in wdk:
            wk = []
            wd = []
        else:
            wk = wdk[key]
            wd = wdd[key]

        #先将日数据转换为周数据
        nwk,nwd = stock.weekK(np.array(k),d)
        #将数据进行合并
        needappend = False
        bi = len(wk)-1 #更新点
        if len(wd)>0:
            for i in range(len(nwk)):
                if not needappend and wd[-1][0] == nwd[i][0]:
                    #覆盖
                    wk[-1][0] = key #id
                    wk[-1][1] = nwk[i][0]#volume
                    wk[-1][2] = nwk[i][4]#close
                    needappend = True
                elif needappend:
                    wd += [nwd[i]]
                    wk += [[key,nwk[i][0],nwk[i][4]]]
            #将id,volume,close转换为volume,open,high,low,close
            wwk = []
            for i in range(len(wk)):
                wwk.append([wk[i][1],0,0,0,wk[i][2]])
            wk = wwk
        else:
            #完全更新
            wk = nwk
            wd = nwd
        #计算周macd,volumema20,energy,volumeJ,boll,bollw
        WK = np.array(wk)
        macd = stock.macdV(WK[:,4])
        volumema20 = stock.ma(WK[:,0],20)
        energy = stock.kdj(stock.volumeEnergy(WK[:,0]))[:,2]
        volumeJ = stock.kdj(WK[:,0])[:,2]
        boll = stock.boll(WK[:,4])
        bollw = stock.bollWidth(boll)
        #将周数据更新到company_status_week表中
        #相等部分更新，后面部分插入
        update_company_status_week(key,WK,macd,volumema20,energy,volumeJ,boll,bollw,wd,bi)
    progress(90)
    #全部更新完成写入最新的更新日期
    stock.execute("update data set status_week_update='%s' where id=1"%(lastday[0][0]))
    stock.closedb()
    progress(100)

"""
用于判断是不是有崛起迹象
istoday 是要使用xueqiu今日数据
"""
def isRasing(a,company,istoday):
    #a[0] a[1] a[2]最近三天的数据a[2]是最近的一天
    #macd 在两日日内有翻红趋势，energy从1以下崛起到大于5，volumeJ趋势向上,close趋势向上
    #0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ
    dMACD = a[2][4]-a[1][4]
    dVolumeJ = a[2][6]-a[1][6]
    dClose = a[2][1]-a[1][1]
    if a[2][4]<0 and a[2][4] + 2*dMACD >= 0 and dVolumeJ>0 and dClose>0 and a[2][5]>=5 and a[1][5]<5:
        return True,[{'x':[-1],'color':'red','linestyle':'--','linewidth':2}]
    return False,[]

#最近50天的status数据
#同时返回50天的日期数组和数据
def redisStatusCache50(db):
    b1,a = shared.numpyFromRedis("%s_last50"%(db))
    b2,d = shared.fromRedis("%s_date50"%(db))
    if not (b1 and b2):
        #缓存中没有准备数据
        d = stock.query("""select date from %s where id=8828 order by date desc limit 50"""%(db))
        d = list(d)
        d.reverse()
        cs=stock.query("""select id,close,volume,volumema20,macd,energy,volumeJ,bollup,bollmid,bolldn,bollw from %s where date>='%s' and date<='%s'"""%(db,stock.dateString(d[0][0]),stock.dateString(d[-1][0])))
        r = stock.query("""select count(*) from company""")
        n = r[0][0] #公司数量
        dn = len(d)
        a = np.ones((n,dn,11))
        lastid = -1
        nc = -1
        temp = []
        for c in cs:
            if c[0]!=lastid:
                if len(temp)>0:
                    offset = dn-len(temp)
                    for i in range(dn):
                        if i<offset:
                            a[nc,i,:] = temp[0]
                        else:
                            a[nc,i,:] = temp[i-offset]
                nc += 1
                lastid = c[0]
                temp = []
                if nc>=n:
                    break
            temp.append(c)
        shared.numpyToRedis(a,"%s_last50"%(db))
        shared.toRedis(d,"%s_date50"%(db))
    #数据d存放的是时间，d[-1]最近的时间 d[0]最远的时间
    #数据a的时间序列和d相同,shape = (公司数,日期,数据)
    return d,a
#companys = [(company_id,code,name,category),....]
#返回
#(datetime,...),K[company,date,(id,close,volume,volumema20,macd,energy,volumeJ,bollup,bollmid,bolldn,bollw)]
#除了id,close,volume其他都是0
def downloadAllK(companys,period,N,progress,ThreadCount=10):
    results = []
    lock = threading.Lock()
    count = 0
    tatoal = len(companys)
    def getk(com):
        nonlocal count,period,N
        b,k_,d_ = xueqiu.K2(com[1],n=N)
        lock.acquire()
        results.append((b,com,k_,d_))
        count-=1
        lock.release()
    for com in companys:
        threading.Thread(target=getk,args=(com,)).start()
        lock.acquire()
        count+=1
        lock.release()
        if progress is not None:
            progress(math.floor(100*len(results)/tatoal))         
        while count>=ThreadCount:
            time.sleep(.1)
    #等等全部处理结束
    while count>0:
        if progress is not None:
            progress(math.floor(100*len(results)/tatoal))   
        time.sleep(.1)
    D = None
    K = np.ones((tatoal,N,11))
    i = 0
    for it in results:
        com = it[1]
        K[i,:,0] = com[0] #id
        if it[0] and len(it[2])==N: #时间上有可能错开，但是短期来说影响不大
            K[i,:,1] = it[2][:,4] #close
            K[i,:,2] = it[2][:,0] #valume
            if D is None:
                D = it[3]
        i+=1
    return D,K
#加速版本
#使用全局变量
_K = None
_D = None
_lastp = None
#返回K = [[[0 id,1 timestamp,2 volume,3 open,4 high,5 low,6 close,7 yesterday_close,8 today_open]
#       ....
#     len(companys)],]
# shape = (len(companys),len(D),7)
#D = [(datetime,),....]
#没有数据返回None,None
def updateRT(companys,N=100,progress=None):
    global _K,_D,_lastp
    b,seqs = shared.fromRedis('runtime_sequence')
    C = len(companys)
    if b:
        if _D is None:
            _D = []
        ba = False if _lastp is not None else True
        if _K is None or len(_K) != C:
            ps = []
            ba = True
        else:
            ps = [_K]
        progress(0)
        i = 0
        seqs = seqs[-N:]
        for ts in seqs:
            if ba:
                b,p = shared.numpyFromRedis("rt%d"%ts)
                if b:
                    if len(p)==C:
                        ps.append(p)
                    elif len(p)>C:
                        ps.append(p[:C])
                    else:
                        pp = np.zeros((C,9))
                        pp[:len(p)] = p
                        ps.append(pp)
                    _D.append((datetime.fromtimestamp(ts/1000000),))
            elif _lastp == ts:
                ba = True
            progress(i/len(seqs))
            i+=1
        if len(ps)>1:
            _K = np.empty((C,len(_D),9))
            bi = 0
            for col in ps:
                if col.shape[0]==C and col.shape[1]==9:
                    ei = bi+1
                    _K[:,bi,:] = col
                else:
                    ei = bi+col.shape[1]
                    _K[:,bi:ei,:] = col
                bi = ei
            #对数据进行不全纠正,有时候close=0表示数据下载错误，可以使用临近的数据进行补全
            if len(ps)>3: #第一次加载完整数据
                for i in range(C):
                    for j in range(1,len(_D)): #从前向后补全
                        if _K[i,j,6]==0 and _K[i,j-1,6]>0:
                            _K[i,j,2:] = _K[i,j-1,2:]                    
                    for j in range(len(_D)-2,-1,-1): #从后向前补全
                        if _K[i,j,6]==0 and _K[i,j+1,6]>0:
                            _K[i,j,2:] = _K[i,j+1,2:]
            else:
                for i in range(C): #增量式补全
                    if _K[i,-1,6]==0 and _K[i,-2,6]>0:
                        _K[i,-1,2:] = _K[i,-2,2:]
                    elif _K[i,-1,6]>0 and _K[i,-2,6]==0:
                        for j in range(len(_D)-2,-1,-1):
                            if _K[i,j,6]==0 and _K[i,j+1,6]>0:
                                _K[i,j,2:] = _K[i,j+1,2:]
            _lastp = seqs[-1]
    if type(N)==int:
        _K = _K[:,-N:,:]
        _D = _D[-N:]
    return _K,_D

"""
K_=[[[0 idd,1 timestamp,2 volume,3 open,4 high,5 low,6 close,7 yesterday_close,8 today_open]
K =[[[(0 idd,1 volume,2 close,3 yesteryday_close,4 today_open)]]]
"""
def downloadAllKFast(companys,progress=None):
    K_,D_ = updateRT(companys,progress=progress)
    if K_ is not None:
        D = D_
        K = np.ones((len(companys),len(D),11))
        K[:,:,0] = K_[:,:,0] #id
        K[:,:,1] = K_[:,:,2] #volume
        K[:,:,2] = K_[:,:,6] #close
        K[:,:,3] = K_[:,:,7] #yesterday_close
        K[:,:,4] = K_[:,:,8] #today_open
        return D,K 
    return None,None
#companys = [(company_id,code,name,category),....]
#返回
#(datetime,...),K[company,date,(0 idd,1 volume,2 close,3 yesteryday_close,4 today_open)]
#除了id,close,volume其他都是0
def loadAllK(companys,bi,ei,period,N,progress,ThreadCount=10):
    results = []
    count = 0
    tatoal = len(companys)
    D = None
    if bi is None:
        if period==5:
            db = 'k5_xueqiu'
            item = 'timestamp'
        else:
            db = 'kd_xueqiu'
            item = 'date'
        d = stock.query("""select %s from %s where id=8828 order by %s desc limit %d"""%(item,db,item,N))
        bi = stock.timeString(d[-1][0])
        ei = stock.timeString(d[0][0])

    for com in companys:
        _,k_,d_ = stock.loadKline(com[1],period,after=bi,ei=ei)
        if d_ is not None and (com[1]=='SH000001' or com[1]=='SZ399001'):
            D = d_
        results.append((True,com,k_,d_))
        count+=1
        if progress is not None:
            progress(math.floor(100*len(results)/tatoal))
    N = len(D)
    K = np.ones((tatoal,N,11))
    i = 0
    for it in results:
        com = it[1]
        K[i,:,0] = com[0] #id
        if it[0] and len(it[2])==N: #时间上有可能错开，但是短期来说影响不大
            K[i,:,1] = it[2][:,0] #valume
            K[i,:,2] = it[2][:,4] #close
            K[i,0,3] = it[2][i,0]
            K[i,1:,3] = it[2][:-1,4] #yesteryday_close
            K[i,:,4] = it[2][:,1] #today_open ,0 volume 1 open 2 high ,3 low 4 close
        i+=1
    return D,K 

#多线程下载加快速度
def downloadXueqiuK15(tasks,progress,tatoal,ThreadCount=10):
    results = []
    lock = threading.Lock()
    count = 0
    #t[0] = [(0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw),...]
    #t[1] = (0 company_id,1 code,2 name,3 category,4 ttm,5 pb)
    def xueqiuK15(t):
        nonlocal count
        b,k_,d_ = xueqiu.xueqiuKday(t[1][1],5)
        lock.acquire()
        results.append({'arg':t,'result':(b,k_,d_)})
        count-=1
        lock.release()

    for t in tasks:
        threading.Thread(target=xueqiuK15,args=((t,))).start()
        lock.acquire()
        count+=1
        lock.release()
        progress(30+math.floor(70*len(results)/tatoal))         
        while count>=ThreadCount:
            time.sleep(.1)
    #等等全部处理结束
    while count>0:
        progress(30+math.floor(70*len(results)/tatoal))   
        time.sleep(.1)
    final_results = []
    for it in results:
        t = it['arg']
        r = it['result']
        k = t[0]
        c = t[1]
        if r[0]: #b
            k0 = r[1][0]
            k1 = r[1][-1]
            #做一个校验，校验上一天的成交量和收盘
            if abs(k[-1][2]/k0[0]-1)>0.05 or abs(k[-1][1]/k0[4]-1)>0.05:
                if abs(k[-1][2]/k0[0]-1)>0.05 and abs(k[-1][1]/k0[4]-1)<0.05:
                    #做一个成交量校正
                    k1[0] *= k[-1][2]/k0[0]
                else:
                    xueqiu.logCheckResult(c[1],15,k[-1],k0)

            idd = c[0]
            A = np.vstack((k,[[idd,k1[4],k1[0],0,0,0,0,0,0,0,0]]))
            #0 id ,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw
            A[-1,4] = stock.macdV(A[:,1])[-1] #macd
            A[-1,5] = stock.kdj(stock.volumeEnergy(A[:,2]))[-1,2] #energy
            A[-1,6] = stock.kdj(A[:,2])[-1,2] #volumeJ
            boll = stock.boll(A[:,1])
            bo = boll[-1] #boll
            A[-1,7] = bo[2] #bollup
            A[-1,8] = bo[1] #bollmid
            A[-1,9] = bo[0] #bolldn
            A[-1,10] = stock.bollWidth(boll)[-1] #bollw
            k = A
            final_results.append((k,c))
    return final_results 

#tasks = [(k,(0 company_id,1 code,2 name,3 category,4 ttm,5 pb))...]
#k = 0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw
#返回[(k,(0 company_id,1 code,2 name,3 category,4 ttm,5 pb))...]
#返回一个系数，代表当前时间成交量应该占全天的比重
def get_tvol(t):
    voltv = [0.097,0.143,0.180,0.212,0.240,0.271,0.298,0.321,0.341,0.361,0.379,0.402,
    0.423,0.439,0.455,0.468,0.480,0.492,0.501,0.514,0.526,0.540,0.555,0.566,
    0.583,0.594,0.606,0.622,0.637,0.647,0.658,0.671,0.682,0.693,0.708,0.722,
    0.736,0.751,0.767,0.784,0.801,0.823,0.847,0.870,0.895,0.920,0.956,1.000]
    hour = t.hour
    mint = t.minute
    for i in range(len(xueqiu.k5date)):
        it = xueqiu.k5date[i]
        if it[0]==hour and it[1]==mint:
            return voltv[i]
    return 1

def downloadRT(tasks,progress):
    result = []
    b,seqs = shared.fromRedis('runtime_sequence')
    if b:
        ts1 = seqs[-1]
        t = datetime.fromtimestamp(ts1/1000000)
        if t.weekday()==0: #星期一
            dt = 3*3600*24*1000*1000
        else:
            dt = 3600*24*1000*1000
        ts0 = ts1-dt
        for ts in seqs:
            if ts>ts0 and ts-ts0<60*1000000:
                ts0 = ts
                break

        b1,p1 = shared.numpyFromRedis("rt%d"%ts1)
        if b1:
            b0,p0 = shared.numpyFromRedis("rt%d"%ts0) #昨天相同时刻
            if b0:
                v0 = p0[:,1]
            else:
                v0 = np.zeros(len(p1)) #简单线性处理
            tv = get_tvol(t)
            idd2inx = {}
            for i in range(len(p1)):
                idd2inx[p1[i,0]] = i
            for it in tasks:
                if it[1][0] in idd2inx:
                    i = idd2inx[it[1][0]]
                    k = it[0]
                    if v0[i]>0:
                        vol =  p1[i,1]*k[-1,2]/v0[i] #这里使用昨天全天的和昨天该时刻的来预测全天的量
                    else:
                        vol = p1[i,1]/tv #使用今天的量仅仅使用分布来推测全天的量
                    if vol>10*k[-1,2]: #别太大
                        vol = 10*k[-1,2]
                    elif vol<0:
                        vol = 0
                    clos = p1[i,5]
                    A = np.vstack((k,[[it[1][0],clos,vol,0,0,0,0,0,0,0,0]]))
                    #0 id ,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw
                    A[-1,4] = stock.macdV(A[:,1])[-1] #macd
                    A[-1,5] = stock.kdj(stock.volumeEnergy(A[:,2]))[-1,2] #energy
                    A[-1,6] = stock.kdj(A[:,2])[-1,2] #volumeJ
                    boll = stock.boll(A[:,1])
                    bo = boll[-1] #boll
                    A[-1,7] = bo[2] #bollup
                    A[-1,8] = bo[1] #bollmid
                    A[-1,9] = bo[0] #bolldn
                    A[-1,10] = stock.bollWidth(boll)[-1] #bollw
                    k = A    
                    result.append((k,it[1]))            
    return result
"""
dd = 
period = 'd','w'
id2companys = {company_id:[0 company_id,1 code,2 name,3 category,4 ttm,5 pb]}
cb 是过滤函数 
"""
def searchRasingCompanyStatusByRT(dd,period,cb,id2companys,progress):
    if period=='d':
        db = 'company_status'
    else:
        db = 'company_status_week'
    progress(10)
    d,a = redisStatusCache50(db)
    progress(30)
    istoday = False
    bi = len(d)-1
    for i in range(len(d)):
        if str(d[i][0])==dd:
            bi = i
    if date.today()==date.fromisoformat(dd):
        istoday = True

    rasing = []
    vlines = {}
    tasks = []
    results = []
    for i in range(len(a)):
        #progress       
        c = a[i]
        idd = int(c[-1][0])
        #反转数组的前后顺序，反转后-1代表最近的数据
        k = c[:bi+1,:]#0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw
        if idd in id2companys:
            if istoday and xueqiu.isTransTime() and period=='d': #将当日数据叠加进数据中
                tasks.append((k,id2companys[idd]))
            else:
                results.append((k,id2companys[idd]))
    
    if len(tasks)>0:
        results = downloadRT(tasks,progress)
    
    for it in results:
        b,vline = cb(it[0],it[1],istoday)
        if b:
            idd = it[1][0]
            rasing.append(idd)
            vlines[idd] = vline

    progress(100)
    return rasing,vlines
#这是使用Redis进行优化的版本    
def searchRasingCompanyStatusByRedis(dd,period,cb,filter,id2companys,progress):
    if period=='d':
        db = 'company_status'
    else:
        db = 'company_status_week'
    progress(10)
    d,a = redisStatusCache50(db)
    progress(30)
    istoday = False
    bi = len(d)-1
    for i in range(len(d)):
        if str(d[i][0])==dd:
            bi = i
    if date.today()==date.fromisoformat(dd):
        istoday = True

    rasing = []
    vlines = {}
    tasks = []
    results = []
    for i in range(len(a)):
        #progress       
        c = a[i]
        idd = int(c[-1][0])
        #反转数组的前后顺序，反转后-1代表最近的数据
        k = c[:bi+1,:]#0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw
        if idd in id2companys and filter(k,id2companys[idd],istoday,period):
            if istoday and xueqiu.isTransTime() and period=='d': #将当日数据叠加进数据中
                tasks.append((k,id2companys[idd]))
            else:
                results.append((k,id2companys[idd]))
    
    if len(tasks)>0:
        results = downloadXueqiuK15(tasks,progress,len(a))
    
    for it in results:
        b,vline = cb(it[0],it[1],istoday)
        if b:
            idd = it[1][0]
            rasing.append(idd)
            vlines[idd] = vline

    progress(100)
    return rasing,vlines

historyRasingCache = [0,0,0,0]
#主要用于观察过去的数据
def searchRasingCompanyStatusByRedisRange(bi,ei,dd,period,cb,filter,id2companys,progress):
    global historyRasingCache
    if historyRasingCache[0]==bi and historyRasingCache[1]==ei:
        d = historyRasingCache[2]
        a = historyRasingCache[3]
    else:
        if period=='d':
            db = 'company_status'
        else:
            db = 'company_status_week'
        #往前延续20天
        bi20 = stock.dateString(date.fromisoformat(bi)-timedelta(days=20))
        d = stock.query("""select date from %s where id=8828 and date>='%s' and date<='%s' order by date desc"""%(db,bi20,ei))
        d = list(d)
        d.reverse()
        cs=stock.query("""select id,close,volume,volumema20,macd,energy,volumeJ,bollup,bollmid,bolldn,bollw from %s where date>='%s' and date<='%s'"""%(db,stock.dateString(d[0][0]),stock.dateString(d[-1][0])))
        r = stock.query("""select count(*) from company""")
        n = r[0][0] #公司数量
        dn = len(d)
        a = np.ones((n,dn,11))
        lastid = -1
        nc = -1
        temp = []
        for c in cs:
            if c[0]!=lastid:
                if len(temp)>0:
                    offset = dn-len(temp)
                    for i in range(dn):
                        if i<offset:
                            a[nc,i,:] = temp[0]
                        else:
                            a[nc,i,:] = temp[i-offset]
                nc += 1
                lastid = c[0]
                temp = []
                if nc>=n:
                    break
            temp.append(c)
        historyRasingCache[0] = bi
        historyRasingCache[1] = ei
        historyRasingCache[2] = d
        historyRasingCache[3] = a              
        #数据d存放的是时间，d[-1]最近的时间 d[0]最远的时间
        #数据a的时间序列和d相同,shape = (公司数,日期,数据)
        #return d,a   
   
    progress(30)
    bii = len(d)-1
    for i in range(len(d)):
        if str(d[i][0])==dd:
            bii = i  
    rasing = []
    vlines = {}
    results = []
    for i in range(len(a)):      
        c = a[i]
        idd = int(c[-1][0])
        #反转数组的前后顺序，反转后-1代表最近的数据
        k = c[:bii+1,:]#0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw
        if idd in id2companys and filter(k,id2companys[idd],False,period):
            results.append((k,id2companys[idd]))
    for it in results:
        b,vline = cb(it[0],it[1],False)
        if b:
            idd = it[1][0]
            rasing.append(idd)
            vlines[idd] = vline
    progress(100)  
    return rasing,vlines
"""
前置过滤器，用于初选。这样在处理当日数据下载时可以少下载很多数据
"""
def defaultFilter(a,c,istoday,period):
    #istoday True可以使用xueqiu数据
    #c [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]
    #a 0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw
    #a[0] a[1] a[2]... a[0]是最近一天的数据
    return True
    """
    if istoday and period=='d':
        return isPopularCategory(c[3])
    else:
        return isPopularCategory(c[3])
    """

"""
按分类列出崛起的股票的数量与列表
"""
def RasingCategoryList(period='d',cb=isRasing,filter=defaultFilter,name=None,bi=None,ei=None):
    today_but = None
    output = widgets.Output()
    output2 = widgets.Output()
    box_layout = Layout(display='flex',
                        flex_flow='wrap',
                        align_items='stretch',
                        border='solid',
                        width='100%')
    progress_layout = Layout(display='flex',
                        flex_flow='wrap',
                        width='100%')                        
    progress = widgets.IntProgress(value=0,
    min=0,max=100,step=1,
    description='Loading:',
    bar_style='',
    orientation='horizontal',layout=progress_layout)
    def progressCallback(p):
        nonlocal progress
        if p < 0:
            p = 0
        if p > 100:
            p = 100
        if math.floor(p)%5==0:
            progress.value = p
        if p == 100:
            progress.close()
    display(progress,output2)

    if period=='d':
        update_status(progressCallback) #更新公司日状态
    else:
        update_status_week(progressCallback)  #更新公司周状态

    #可以提前准备的数据
    categorys = stock.query("""select id,name from category""")
    companys = stock.query("""select company_id,code,name,category,ttm,pb from company_select""")
    if bi is not None:
        dates = stock.query("select date from %s where id=8828 and date>='%s' and date<='%s' order by date desc"%('company_status' if period=='d' else 'company_status_week',bi,ei))
    else:
        dates = stock.query('select date from %s where id=8828 order by date desc limit 50'%('company_status' if period=='d' else 'company_status_week'))

    id2companys = {}
    for c in companys:
        id2companys[c[0]] = c
    
    prevClickButton = None
    prevClickButtonStyle = None
    #点击日期
    def onCatsList(E):
        nonlocal progress,prevClickButton,prevClickButtonStyle
        if prevClickButton is not None:
            prevClickButton.button_style = prevClickButtonStyle
        prevClickButton = E
        prevClickButtonStyle = E.button_style
        E.button_style = 'warning' #选择时的高亮

        progress = widgets.IntProgress(value=0,
            min=0,max=100,step=1,
            description='Loading:',
            bar_style='',
            orientation='horizontal',layout=progress_layout)
        with output2:
            display(progress)            
        progressCallback(0)
        if bi is None:
            rasing,vlines = searchRasingCompanyStatusByRT(E.date,period,cb,id2companys,progressCallback)
        else:
            rasing,vlines = searchRasingCompanyStatusByRedisRange(bi,ei,E.date,period,cb,filter,id2companys,progressCallback)
        cats = {}
        rasingCompany = []
        for c in companys:
            if c[0] in rasing:
                rasingCompany.append(c)
        # cats = {"id":{"name":,"ls":,"count":0}}
        for c in categorys:
            if c[1] not in cats:
                cats[c[1]] = {"name":c[1],"ls":[],"count":0}
        for c in companys:
            if c[0] in rasing and c[3] in cats:
                cats[c[3]]['ls'].append(c)
                cats[c[3]]['count'] += 1
        #计算分类中的崛起数量，不列出那些没有崛起的分类
        items = []
        #计算从当前日期
        current_date = date.fromisoformat(E.date)

        def index2date(inx):
            if current_date==today:
                if inx == -1:
                    return today
                else:
                    return dates[-inx-2][0]
            for i in range(len(dates)):
                d = dates[i][0]
                if current_date==d:
                    return dates[i-inx-1][0]
            return None
        #点击分类
        prevCatButton = None
        preCatButtonStyle = None
        def onClick(e):
            nonlocal prevCatButton,preCatButtonStyle,E,vlines
            if prevCatButton is not None:
                prevCatButton.button_style = preCatButtonStyle
            prevCatButton = e
            preCatButtonStyle = e.button_style
            e.button_style = 'warning'
            key = e.tooltip
            output.clear_output(wait=True)
            with output:
                display(box)
                for c in cats[key]['ls']:
                    #对vlines的位置是相对于当前日期，因此需要做偏移调整
                    vls = copy.deepcopy(vlines[c[0]])
                    lastdd = None
                    for vline in vls:
                        if 'x' in vline:
                            vline['dates'] = []
                            for i in vline['x']:
                                lastdd = index2date(i)
                                vline['dates'].append(index2date(i)) #将负索引转换为日期
                    #kline.Plote(c[1],period,config={"index":True,"markpos":current_date,"vlines":vls}).show(figsize=(32,15))
                    kline.Plote(c[1],period,config={"index":True,"vlines":vls},mode="auto").show(figsize=(32,15),pos=lastdd)
        
        sortedKeys = sorted(cats,key=lambda it:cats[it]['count'],reverse=True)
        count = 0
        for c in sortedKeys:
            if cats[c]["count"]>0:
                s = "%s %d"%(cats[c]["name"],cats[c]["count"])
                but = widgets.Button(
                    description=s,
                    disabled=False,
                    button_style='',
                    tooltip=c)
                but.on_click(onClick)
                items.append(but)
                count+=cats[c]["count"]
        E.description = E.date+' ('+str(count)+')'
        #将数据记录到redis中去过期20天过期
        if name is not None:
            shared.toRedis(count,name+'@'+E.date,ex=20*24*3600) #20天后过期
        box = Box(children=items, layout=box_layout)
        output.clear_output(wait=True)
        with output:
            display(box)

    items = []

    today = date.today()
    
    if period=='d' and dates[0][0] != today:
        #如果今天是一个交易日，并且不在数据库中，那么从雪球直接下载数据
        today_but = widgets.Button(
            description=str(today),
            disabled=False,
            button_style='danger')
        today_but.date = str(today)
        today_but.on_click(onCatsList)
        items.append(today_but)
    
    if bi is not None:
        N = len(dates)
    else:
        N = 15
    for i in range(N):
        d = dates[i]
        desc = str(d[0])
        if name is not None:
            b,count = shared.fromRedis(name+'@'+str(d[0]))
            if b:
                desc = str(d[0])+' ('+str(count)+')'
        but = widgets.Button(
            description=desc,
            disabled=False,
            button_style='')
        but.date = str(d[0])
        but.on_click(onCatsList)
        items.append(but)

    box = Box(children=items, layout=box_layout)
    display(box,output)

    def updatek15():
        nonlocal today_but
        if xueqiu.isTransTime():
            today_but.button_style = 'success' #green button
            xueqiu.Timer(xueqiu.nextdt15()+1,updatek15)
    if today_but is not None:
        xueqiu.Timer(xueqiu.nextdt15()+1,updatek15)

#最近N天的status数据
#同时返回N天的日期数组和数据
def getStatusN(db='company_status',N=50,bi=None,ei=None):
    #缓存中没有准备数据
    if bi is not None:
        d = stock.query("""select date from %s where id=8828 and date>='%s' and date<='%s' order by date desc"""%(db,bi,ei))
    else:
        d = stock.query("""select date from %s where id=8828 order by date desc limit %d"""%(db,N))
    d = list(d)
    d.reverse()
    cs=stock.query("""select id,close,volume,volumema20,macd,energy,volumeJ,bollup,bollmid,bolldn,bollw from %s where date>='%s' and date<='%s'"""%(db,stock.dateString(d[0][0]),stock.dateString(d[-1][0])))
    r = stock.query("""select count(*) from company""")
    n = r[0][0] #公司数量
    dn = len(d)
    a = np.ones((n,dn,11))
    lastid = -1
    nc = -1
    temp = []
    for c in cs:
        if c[0]!=lastid:
            if len(temp)>0:
                offset = dn-len(temp)
                for i in range(dn):
                    if i<offset:
                        a[nc,i,:] = temp[0]
                    else:
                        a[nc,i,:] = temp[i-offset]
            nc += 1
            lastid = c[0]
            temp = []
            if nc>=n:
                break
        temp.append(c)
    #数据d存放的是时间，d[-1]最近的时间 d[0]最远的时间
    #数据a的时间序列和d相同,shape = (公司数,日期,数据)
    return d,a

"""
返回
周期n表示相比n天前或者n个前的增长
这里做一个扩展当周期是'd'时,周期盈利将变成日盈利(和昨日收盘进行比较)
[
    (0 周期,
     1 分类名称,
     2 周期盈利二维数组np.array[company_n,date_n],
     3 日期列表[(date,),...],
     4 np.array[(0 id , 1 code , 2 name , 3 category),],
     5 按周期利润排序的索引和利润对[company,date,(index,dk)],
     6 该分类的前十名平均盈利[date_n],
     7 该分类的跌幅前十的平均跌幅[date_n]
     8 (0前面10名的成交量最近5分钟) ？
     )
]
K = [company_n,date_n,(0 idd,1 volume,2 close,3 yesteryday_close,4 today_open)]
D = [(date,)...]
#使用线程加速 ,单线程更快，测试结果多线程用时4s,单线程用2s
"""
def processKD2_CB(K,D,companys,topN=20,progress=None): #对processKD2的优化，只有在需要的时候才处理数据
    id2com = {}

    progress(0)
    for com in companys:
        id2com[com[0]] = com

    idd = np.empty((len(K),4),dtype=np.dtype('O')) #(0 id , 1 code , 2 name , 3 category)
    idd[:,0] = K[:,0,0]
    for i in idd:
        k = int(i[0])
        if k in id2com:
            i[1] = id2com[k][1]
            i[2] = id2com[k][2]
            i[3] = id2com[k][3]

    def calcDayCB(day):
        nonlocal idd,id2com,result,K,D,topN
        result = []
        if day=='d':
            dk = np.zeros((len(K),len(D)))
            for i in range(len(K)):
                if not (K[i,:,3]==0).any():
                    dk[i,:] = K[i,:,2]/K[i,:,3]-1 #收盘相对昨天收盘的增长率
        else:
            ma5 = np.empty((K.shape[0],K.shape[1])) #收盘价5日均线
            for i in range(len(K)):
                ma5[i,:] = stock.ma(K[i,:,2],5)
                eqz = ma5[i,:]==0
                if eqz.any():
                    ma5[i,eqz] = 1 #确保不会等于0,避免被零除错误
                    K[i,eqz,2] = 1 #确保这些计算处理的dk = 0
            dk = K[:,day:,2]/ma5[:,:-day]-1#收盘相对day前的增长率
        for category in allCategory():
            r = idd[:,3]==category
            dK = dk[r]
            if len(dK)>0:
                sorti = np.zeros((dK.shape[0],dK.shape[1],2))
                ia = np.zeros((dK.shape[0],2))
                ia[:,0] = np.arange(dK.shape[0])
                for i in range(dK.shape[1]):
                    ia[:,1] = dK[:,i]
                    sorti[:,i,:] = np.array(sorted(ia,key=lambda it:it[1],reverse=True))

                top10mean = np.zeros((dK.shape[1]))
                low10mean = np.zeros((dK.shape[1]))
                for i in range(dK.shape[1]):
                    top10mean[i] = sorti[:topN,i,1].mean()
                    low10mean[i] = sorti[-topN:,i,1].mean()
                if day=='d':
                    result.append((day,category,dK,D[:],idd[r],sorti,top10mean,low10mean))
                else:
                    result.append((day,category,dK,D[day:],idd[r],sorti,top10mean,low10mean))
            else:
                print("'%s' 分类里面没有公司"%category)
    
    return calcDayCB

def processKD2(days,K,D,companys,topN=20,progress=None):
    result = []
    id2com = {}
    progress(0)
    for com in companys:
        id2com[com[0]] = com

    idd = np.empty((len(K),4),dtype=np.dtype('O')) #(0 id , 1 code , 2 name , 3 category)
    idd[:,0] = K[:,0,0]
    for i in idd:
        k = int(i[0])
        if k in id2com:
            i[1] = id2com[k][1]
            i[2] = id2com[k][2]
            i[3] = id2com[k][3]
    j=0
    for day in days:
        if day=='d':
            dk = np.zeros((len(K),len(D)))
            for i in range(len(K)):
                if not (K[i,:,3]==0).any():
                    dk[i,:] = K[i,:,2]/K[i,:,3]-1 #收盘相对昨天收盘的增长率
        else:
            ma5 = np.empty((K.shape[0],K.shape[1])) #收盘价5日均线
            for i in range(len(K)):
                ma5[i,:] = stock.ma(K[i,:,2],5)
                eqz = ma5[i,:]==0
                if eqz.any():
                    ma5[i,eqz] = 1 #确保不会等于0,避免被零除错误
                    K[i,eqz,2] = 1 #确保这些计算处理的dk = 0
            dk = K[:,day:,2]/ma5[:,:-day]-1#收盘相对day前的增长率
        for category in allCategory():
            r = idd[:,3]==category
            dK = dk[r]
            if len(dK)>0:
                sorti = np.zeros((dK.shape[0],dK.shape[1],2))
                ia = np.zeros((dK.shape[0],2))
                ia[:,0] = np.arange(dK.shape[0])
                for i in range(dK.shape[1]):
                    ia[:,1] = dK[:,i]
                    sorti[:,i,:] = np.array(sorted(ia,key=lambda it:it[1],reverse=True))

                top10mean = np.zeros((dK.shape[1]))
                low10mean = np.zeros((dK.shape[1]))
                for i in range(dK.shape[1]):
                    top10mean[i] = sorti[:topN,i,1].mean()
                    low10mean[i] = sorti[-topN:,i,1].mean()
                if day=='d':
                    result.append((day,category,dK,D[:],idd[r],sorti,top10mean,low10mean))
                else:
                    result.append((day,category,dK,D[day:],idd[r],sorti,top10mean,low10mean))
            else:
                print("'%s' 分类里面没有公司"%category)
        progress(j/len(days))
        j+=1
    return result

def processKD(days,K,D,companys,topN=10):
    result = []
    id2com = {}
    for com in companys:
        id2com[com[0]] = com

    idd = np.empty((len(K),4),dtype=np.dtype('O')) #(0 id , 1 code , 2 name , 3 category)
    idd[:,0] = K[:,0,0]
    for i in idd:
        k = int(i[0])
        if k in id2com:
            i[1] = id2com[k][1]
            i[2] = id2com[k][2]
            i[3] = id2com[k][3]

    for day in days:
        ma5 = np.empty((K.shape[0],K.shape[1])) #收盘价5日均线
        for i in range(len(K)):
            ma5[i,:] = stock.ma(K[i,:,1],5)
            ma5[i,ma5[i,:]==0] = 1 #确保不会等于0
        dk = (K[:,day:,1]-ma5[:,:-day])/ma5[:,:-day]#收盘相对day前的增长率
        for category in allCategory():
            r = idd[:,3]==category
            dK = dk[r]
            if len(dK)>0:
                sorti = np.zeros((dK.shape[0],dK.shape[1],2))
                ia = np.zeros((dK.shape[0],2))
                ia[:,0] = np.arange(dK.shape[0])
                for i in range(dK.shape[1]):
                    ia[:,1] = dK[:,i]
                    sorti[:,i,:] = np.array(sorted(ia,key=lambda it:it[1],reverse=True))

                top10mean = np.zeros((dK.shape[1]))
                low10mean = np.zeros((dK.shape[1]))
                for i in range(dK.shape[1]):
                    top10mean[i] = sorti[:10,i,1].mean()
                    low10mean[i] = sorti[-10:,i,1].mean()
                result.append((day,category,dK,D[day:],idd[r],sorti,top10mean,low10mean))
            else:
                print("'%s' 分类里面没有公司"%category)
    return result

def StrongSorted(days,N=50,bi=None,ei=None,topN=20,progress=None,companys=None):
    if bi is not None:
        if ei is not None:
            D,K = getStatusN(bi=bi,ei=ei)
        else:
            D,K = getStatusN(bi=bi,ei=stock.dateString(date.today()))
    else:
        if N>50:
            D,K = getStatusN(N=N)
        else:
            D,K = redisStatusCache50('company_status')
    # K = [(0 idd,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw)]
    # K_ = [(0 idd,1 volume,2 close,3 yesteryday_close,4 today_open)]
    K_ = np.zeros((len(K),len(D),5))
    K_[:,:,0] = K[:,:,0]
    K_[:,:,1] = K[:,:,2]
    K_[:,:,2] = K[:,:,1]
    #舍弃3 yesteryday_close,4 today_open
    return processKD2(days,K_,D,companys,topN=topN,progress=progress)
  
def StrongSorted5k(days,N=50,bi=None,ei=None,topN=20,progress=None,companys=None):
    progress(0)
    D,K = loadAllK(companys,bi,ei,5,N,progress)
    progress(100)
    if D is None or K is None:
        return []
    return processKD2(days,K,D,companys,topN=topN,progress=progress)

def StrongSortedRT(days,topN=20,progress=None,companys=None):
    progress(0)
    def progress0_50(i):
        progress(i/2)
    def progress50_100(i):
        progress(i/2+50)
    D,K = downloadAllKFast(companys,progress0_50)
    if D is None or K is None:
        return []
    result = processKD2(days,K,D,companys,topN=topN,progress=progress50_100)    
    progress(100)
    return result

mycolors=[
    "red",
    "purple",    
    "black",
    "blue",
    "brown",
    "tomato",    
    "darkslategrey",
    "aqua",    
    "darkmagenta",    
    "chartreuse",
    "chocolate",
    "coral",
    "crimson",
    "darkblue",
    "darkgreen",
    "fuchsia",
    "gold",
    "green",
    "grey",
    "indigo",
    "lime",
    "magenta",
    "maroon",
    "navy",
    "olive",
    "orange",
    "orangered",
    "orchid",
    "pink",
    "plum",
    "darkred",
    "salmon",
    "sienna",
    "tan",
    "teal",
    "violet",
    "yellow"
]
name2int = {}
namecount = 0
def getmycolor(name):
    global mycolors,name2int,namecount
    if name in name2int:
        return mycolors[name2int[name]]
    
    name2int[name] = namecount%len(mycolors)
    namecount += 1
    return mycolors[name2int[name]]

def PlotCategory(bi,ei,pos,r,top=None,focus=None,cycle='d',output=None):
    fig,axs = plt.subplots(figsize=(28,14))
    dd = r[3] #date
    if cycle=='d' or cycle==5:
        axs.xaxis.set_major_formatter(kline.MyFormatter(dd,cycle))
    else:
        axs.xaxis.set_major_formatter(MyFormatterRT(dd))
    if top is None:
        axs.set_title("%s 周期%s"%(r[1],r[0]))
    else:
        axs.set_title("%s 周期%s Top%s"%(r[1],r[0],top))

    def getCompanyRank(name,j,rank):
        return ''
    xdd = np.arange(len(dd))
    if top is None:
        for i in range(len(r[2])):
            dk = r[2][i] #
            idd = r[4][i]
            if focus is not None:
                if idd[2]==focus:
                    axs.plot(xdd[bi:ei],dk[bi:ei],linewidth=2,label = idd[2])
                else:
                    axs.plot(xdd[bi:ei],dk[bi:ei],alpha=0.2,label = idd[2])
            else:        
                axs.plot(xdd[bi:ei],dk[bi:ei],label = idd[2])
    else:
        isplot = False
        rank = 1
        for d in r[5][:top+1,pos,:]:
            i = int(d[0])
            dk = r[2][i] #
            idd = r[4][i]
            if pos-1>=0:
                title = "%d %s %s"%(rank,idd[2],getCompanyRank(idd[2],pos-1,rank))
            else:
                title = "%d %s"%(rank,idd[2])
            color = getmycolor(idd[2])
            if focus is not None:
                if idd[2]==focus:
                    axs.plot(xdd[bi:ei],dk[bi:ei],linewidth=3,label = title,color=color)
                    isplot = True
                else:
                    axs.plot(xdd[bi:ei],dk[bi:ei],alpha=0.2,label = title,color=color)
            else:        
                axs.plot(xdd[bi:ei],dk[bi:ei],label = title,color=color)
            rank+=1
        if not isplot:
            for i in range(len(r[2])):
                dk = r[2][i] #
                idd = r[4][i]
                color = getmycolor(idd[2])
                title = "%d %s"%(rank,idd[2])
                if focus is not None:
                    if idd[2]==focus:
                        axs.plot(xdd[bi:ei],dk[bi:ei],linewidth=2,linestyle='--',label = title,color=color)
                rank+=1
    axs.axvline(pos,color="red",linewidth=2,linestyle='--')
    xticks=[]
    for i in range(bi,ei):
        xticks.append(i)
    xticks.append(pos)
    axs.set_xticks(xticks)
    axs.grid(True)
    axs.axhline(0,color='black',linewidth=1,linestyle='--')
    axs.set_xlim(bi,ei-1)
    plt.legend(bbox_to_anchor=(1, 1),loc='upper left',fontsize='large')
    fig.autofmt_xdate()
    if output is None:
        plt.show()
    else:
        kline.output_show(output)

"""
按分类列出强势股
"""
def StrongCategoryCompanyList(category,name,toplevelpos=None,period=20,periods=[3,5,10,20],cycle='d',sortType='TOP10'):
    def getResult(day,categoryName):
        nonlocal category
        for r in category:
            if r[0]==day and r[1]==categoryName:
                return r
        return None

    top = 10
    com = None
    result = getResult(period,name)
    pagecount = 50
    LEN = len(result[3])
    bi = LEN-pagecount
    ei = LEN   
    if toplevelpos is not None:
        pos = toplevelpos
        if pos>LEN:
            pos = LEN-1
        bi = pos-math.floor(pagecount/2)
        if bi<0:
            bi = 0
        ei = bi+pagecount
        if ei>=LEN:
            ei = LEN-1
            bi = ei-pagecount
    else:
        pos = LEN-1
    if bi < 0:
        bi = 0

    output = widgets.Output()
    output2 = widgets.Output()
    
    idd = result[4]
    def getCodeByName(name):
        for it in idd:
            if it[2]==name:
                return it[1]
        return 'None'

    nextbutton = widgets.Button(description="下一页",layout=Layout(width='96px'))
    prevbutton = widgets.Button(description="上一页",layout=Layout(width='96px'))
    zoominbutton = widgets.Button(description="+",layout=Layout(width='48px'))
    zoomoutbutton = widgets.Button(description="-",layout=Layout(width='48px'))
    nextbutton = widgets.Button(description="下一页",layout=Layout(width='96px'))
    prevbutton = widgets.Button(description="上一页",layout=Layout(width='96px'))
    zoominbutton = widgets.Button(description="+",layout=Layout(width='48px'))
    zoomoutbutton = widgets.Button(description="-",layout=Layout(width='48px'))

    backbutton = widgets.Button(description="<",layout=Layout(width='48px'))
    frontbutton = widgets.Button(description=">",layout=Layout(width='48px'))
    slider = widgets.IntSlider(
        value=ei,
        min=bi,
        max=ei,
        step=1,
        description='',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=False,
        layout=Layout(width='128px')
        #readout=True,
        #readout_format='d'
    )

    periodDropdown = widgets.Dropdown(
        options=periods,
        value=period,
        description='周期',
        layout=Layout(display='block',width='96px'),
        disabled=False)
    topDropdown = widgets.Dropdown(
        options=[3,5,10,20,30,100],
        value=top,
        description='排名',
        layout=Layout(display='block',width='96px'),
        disabled=False)

    comDropdown = widgets.Dropdown(
        options=[],
        value=None,
        description='公司',
        layout=Layout(display='block',width='196px'),
        disabled=False)
    butList = widgets.Button(
        description='列表',
        disabled=False,
        button_style='',
        layout=Layout(width='64px'),
        tooltip='列出股票的图表')
    def onListClick(e):
        nonlocal top,pos,result,name,cycle
        output2.clear_output(wait=True)
        with output2:
            for i in range(top):
                if i < len(result[5]):
                    inx = int(result[5][i,pos,0])
                    r = result[4][inx] #(0 id , 1 code , 2 name , 3 category)
                    dd = result[3][pos][0]
                    kline.Plote(r[1],'d',config={'index':True,'markpos':dd},context="强势分类 %s %d"%(name,i+1),mode="auto").show()

    butList.on_click(onListClick)
    out = widgets.Output()
    box_layout = Layout(display='flex',
                    flex_flow='wrap',
                    align_items='stretch',
                    border='solid',
                    width='100%')    
    stopUpdate = False
    def sortCompanyList():
        nonlocal pos,result,periodDropdown,stopUpdate,sortType
        stopUpdate = True
        idd = result[4] #(0 id , 1 code , 2 name , 3 category)
        coms = [None]
        for it in result[5][:,pos]:
            coms.append(idd[int(it[0])][2])
        sel = comDropdown.value
        comDropdown.options = coms
        comDropdown.value = sel
        stopUpdate = False

    sortCompanyList()
    needUpdateSlider = True
    def showPlot():
        nonlocal bi,ei,pos,stopUpdate,needUpdateSlider,cycle
        if stopUpdate:
            return
        #output.clear_output(wait=True)
        #with output:
        PlotCategory(bi,ei,pos,result,top=top,focus=com,cycle=cycle,output=output)
        needUpdateSlider = True

    def setSlider(minv,maxv,value):
        nonlocal slider,needUpdateSlider
        needUpdateSlider = False
        if minv>slider.max:
            slider.max = maxv
            slider.min = minv
        else:
            slider.min = minv
            slider.max = maxv
        slider.value = value

    def on_period(e):
        nonlocal result,comDropdown,period,name,bi,ei,pos,LEN,com
        period = e['new']
        result = getResult(period,name)
        LEN = len(result[3])
        bi = LEN-pagecount
        ei = LEN-1
        pos = LEN-1
        if bi < 0:
            bi = 0
        setSlider(bi,ei,pos)
        sortCompanyList()
        showPlot()

    periodDropdown.observe(on_period,names='value')

    def on_top(e):
        nonlocal top
        top = e['new']
        showPlot()

    topDropdown.observe(on_top,names='value')

    def on_com(e):
        nonlocal com,box,stopUpdate,pos,result,cycle
        com = e['new']
        if stopUpdate:
            return
        if com is None:
            out.clear_output()
            output2.clear_output()
        else:
            out.clear_output(wait=True)
            #with out:
            #    display(widgets.HTML(value="""<a href="https://xueqiu.com/S/%s" target="_blank" rel="noopener">%s</a>"""%(getCodeByName(com),com)))             
        
        if com is None:                
            showPlot()
        else:
            showPlot()
            output2.clear_output(wait=True)
            with output2:
                dd = result[3][pos][0]
                kline.Plote(getCodeByName(com),'d',config={'index':True,'markpos':dd},context="强势分类 %s"%(name),mode="auto").show()

    comDropdown.observe(on_com,names='value')

    def on_prev(e):
        nonlocal bi,ei,pos,pagecount,LEN
        bi -= pagecount
        if bi<0:
            bi = 0
        ei = bi+pagecount
        if ei>=LEN:
            ei = LEN-1
        pos = ei
        setSlider(bi,ei,pos)            
        showPlot()
    def on_next(e):
        nonlocal bi,ei,pos,pagecount,LEN
        ei += pagecount
        if ei>=LEN:
            ei = LEN-1
        bi = ei-pagecount
        if bi<0:
            bi = 0
        pos = ei
        setSlider(bi,ei,pos)            
        showPlot()
    def on_zoomin(e):
        nonlocal bi,ei,pos,pagecount,LEN
        if pagecount > 30:
            pagecount -= 10
            bi = ei-pagecount
            if bi<0:
                bi = 0
                ei = bi+pagecount
                if ei>LEN:
                    ei = LEN-1
                pos = ei
                setSlider(bi,ei,pos)
            showPlot()
    def on_zoomout(e):
        nonlocal bi,ei,pos,pagecount,LEN
        if pagecount < 190:
            pagecount += 10
            bi = ei-pagecount
            if bi<0:
                bi = 0
                ei = bi+pagecount
                if ei>LEN:
                    ei = LEN-1
                pos = ei
                setSlider(bi,ei,pos)
            showPlot()

    def on_prevpos(e):
        nonlocal pos,bi,ei,slider,needUpdateSlider
        pos -= 1
        if pos<0:
            pos=0
        needUpdateSlider = False
        slider.value = pos
        showPlot()
    def on_nextpos(e):
        nonlocal pos,bi,ei,LEN,slider,needUpdateSlider
        pos += 1
        if pos>=LEN:
            pos=LEN-1
        needUpdateSlider = False
        slider.value = pos
        showPlot()
    def on_sliderChange(e):
        nonlocal pos,needUpdateSlider,LEN
        pos = e['new']
        if pos>=LEN:
            pos = LEN-1
        sortCompanyList()
        if needUpdateSlider:
            showPlot()

    prevbutton.on_click(on_prev)
    nextbutton.on_click(on_next)
    zoominbutton.on_click(on_zoomin)
    zoomoutbutton.on_click(on_zoomout)
    backbutton.on_click(on_prevpos)
    frontbutton.on_click(on_nextpos) 
    slider.observe(on_sliderChange,names='value') 
    if LEN <= pagecount:
        box = Box(children=[backbutton,slider,frontbutton,periodDropdown,topDropdown,butList,comDropdown,out],layout=box_layout)
    else:
        box = Box(children=[prevbutton,nextbutton,zoominbutton,zoomoutbutton,backbutton,slider,frontbutton,periodDropdown,topDropdown,butList,comDropdown,out],layout=box_layout)
    display(box,output,output2)
    showPlot()

def PlotAllCategory(bi,ei,pos,sortedCategory,pervSortedCategory,top,focus=None,cycle='d',output=None):
    fig,axs = plt.subplots(figsize=(28,14))
    r = sortedCategory[0]
    dd = r[3] #date

    if cycle=='d' or cycle==5:
        axs.xaxis.set_major_formatter(kline.MyFormatter(dd,cycle))
    else:
        axs.xaxis.set_major_formatter(MyFormatterRT(dd,cycle))
    if top is None:
        axs.set_title("%s 周期%s"%(r[1],r[0]))
    else:
        axs.set_title("%s 周期%s Top%s"%(r[1],r[0],top))
    
    i = 0
    xdd = np.arange(len(dd))
    def isFocusIt(focus,categoryName,i,top):
        v = (i+1)/top
        if focus=='1/5':
            return v<=1/5
        elif focus=='2/5':
            return v<=2/5 and v>1/5
        elif focus=='3/5':
            return v<=3/5 and v>2/5
        elif focus=='4/5':
            return v<=4/5 and v>2/5
        elif focus=='5/5':
            return v<=5/5 and v>4/5
        else:
            return focus==categoryName
    def getPrevRank(name,j):
        for i in range(len(pervSortedCategory)):
            r = pervSortedCategory[i]
            if r[1]==name:
                if i-j>0:
                    return '+%d'%(i-j)
                elif i-j<0:
                    return str(i-j)
                else:
                    return ''
        return ''
    for r in sortedCategory:
        color = getmycolor(r[1])
        dk = r[6] #
        if pervSortedCategory is None:
            title = "%d %s"%(i+1,r[1])
        else:
            title = "%d %s %s"%(i+1,r[1],getPrevRank(r[1],i))
        if top is not None:
            if i<top:
                if focus is not None:
                    if isFocusIt(focus,r[1],i,top):
                        axs.plot(xdd[bi:ei],dk[bi:ei],linewidth=3,label = title,color=color)
                    else:
                        axs.plot(xdd[bi:ei],dk[bi:ei],alpha=0.2,label = title,color=color)
                else:        
                    axs.plot(xdd[bi:ei],dk[bi:ei],label = title,color=color)
            else:
                if focus is not None and isFocusIt(focus,r[1],i,top):
                    axs.plot(xdd[bi:ei],dk[bi:ei],linewidth=3,linestyle='--',label = title,color=color)
        i+=1
    axs.axvline(pos,color="red",linewidth=2,linestyle='--')
    xticks=[]
    for i in range(bi,ei):
        xticks.append(i)
    xticks.append(pos)
    axs.set_xticks(xticks)
    axs.grid(True)
    axs.axhline(0,color='black',linewidth=1,linestyle='--')
    axs.set_xlim(bi,ei-1)
    plt.legend(bbox_to_anchor=(1, 1),loc='upper left',fontsize='large')
    fig.autofmt_xdate()
    if output is None:
        plt.show()
    else:
        kline.output_show(output)

"""
强势分类于强势股
N 最近多少天的数据,50天的话可以使用redis速度较快
bi 开始时间
ei 结束时间
N 和 bi,ei只能选择一种
"""
def StrongCategoryList(N=50,cycle='d',bi=None,ei=None):
    companys = stock.query("""select company_id,code,name,category from company_select""")
    out2 = widgets.Output()
    progress = widgets.IntProgress(value=0,
    min=0,max=100,step=1,
    description='download',
    bar_style='',
    orientation='horizontal',layout=Layout(display='flex',
                        flex_flow='wrap',
                        width='100%'))
    done = False
    def progressCallback(p):
        nonlocal progress,done
        if p < 0:
            p = 0
        if p > 100:
            p = 100
        if math.floor(p)%5==0:
            progress.value = p
        if done:
            progress.close()
            out2.clear_output()
    display(out2)
    with out2:
        display(progress)
    sample = 20
    update_status(progressCallback) #更新公司日状态
    if cycle=='d':
        periods = [3,5,10,20]
        period = 20
        result = StrongSorted(periods,N,bi=bi,ei=ei,topN=sample,progress=progressCallback,companys=companys)
    elif cycle==5:
        periods = [1,3,6]
        period = 3
        result = StrongSorted5k(periods,N,bi=None,ei=None,topN=sample,progress=progressCallback,companys=companys)
    else: #实时
        periods = [3,15,45,'d']
        period = 15
        result = StrongSortedRT(periods,topN=sample,progress=progressCallback,companys=companys)

    done = True
    sortType = 'TOP10'
    progressCallback(100)
    output = widgets.Output()
    def getSortedCategory(day,pos):
        nonlocal sortType
        categorys = []
        if len(result)==0:
            return []
        for r in result:
            if r[0]==day:
                categorys.append(r)
        if pos > len(categorys[0][6])-1:
            pos = len(categorys[0][6])-1
        if pos < -len(categorys[0][6]):
            pos = -len(categorys[0][6])                
        if sortType=='TOP10':
            return sorted(categorys,key=lambda it:it[6][pos],reverse=True)
        elif sortType=='TOP10倒序':
            return sorted(categorys,key=lambda it:it[6][pos])
        elif sortType=='LOW10':
            return sorted(categorys,key=lambda it:it[7][pos])
        else: #'弱势跌幅榜':
            return sorted(categorys,key=lambda it:it[7][pos],reverse=True)
    
    sortedCategory = getSortedCategory(period,-1)
    top = 30
    mark = None
    category = None
    pagecount = 50
    LEN = len(sortedCategory[0][3])
    bi = LEN-pagecount
    ei = LEN
    pos = LEN-1
    if bi < 0:
        bi = 0
    def markListItem():
        nonlocal sortedCategory
        sortedCategoryNames = [None]
        for it in sortedCategory:
            sortedCategoryNames.append(it[1])
        return sortedCategoryNames+['1/5','2/5','3/5','4/5','5/5']
    def categoryListItem():
        nonlocal sortedCategory
        sortedCategoryNames = [None]
        for it in sortedCategory:
            sortedCategoryNames.append(it[1])
        return sortedCategoryNames
    nextbutton = widgets.Button(description="下一页",layout=Layout(width='96px'))
    prevbutton = widgets.Button(description="上一页",layout=Layout(width='96px'))
    zoominbutton = widgets.Button(description="+",layout=Layout(width='48px'))
    zoomoutbutton = widgets.Button(description="-",layout=Layout(width='48px'))
    backbutton = widgets.Button(description="<",layout=Layout(width='48px'))
    frontbutton = widgets.Button(description=">",layout=Layout(width='48px'))
    slider = widgets.IntSlider(
        value=pos,
        min=bi,
        max=ei,
        step=1,
        description='',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=False,
        layout=Layout(width='128px')
        #readout=True,
        #readout_format='d'
    )
    periodDropdown = widgets.Dropdown(
        options=periods,
        value=period,
        description='周期',
        layout=Layout(display='block',width='96px'),
        disabled=False)
    topDropdown = widgets.Dropdown(
        options=[3,5,10,20,30,50,108],
        value=top,
        description='排名',
        layout=Layout(display='block',width='96px'),
        disabled=False)
    sampleDropdown = widgets.Dropdown(
        options=[1,2,3,5,10,20,30,50,100],
        value=sample,
        description='样本',
        layout=Layout(display='block',width='96px'),
        disabled=False)    
    listDropdown = widgets.Dropdown(
        options=[None,3,5,10,20,30],
        value=None,
        description='列表',
        layout=Layout(display='block',width='100px'),
        disabled=False)
    markDropdown = widgets.Dropdown(
        options=markListItem(),
        value=mark,
        description='高亮',
        layout=Layout(display='block',width='215px'),
        disabled=False)        
    categoryDropdown = widgets.Dropdown(
        options=categoryListItem(),
        value=category,
        description='选择分类',
        layout=Layout(display='block',width='215px'),
        disabled=False)
    resverdDropdown = widgets.Dropdown(
        options=['TOP10','TOP10倒序','LOW10','LOW10倒序'],
        value='TOP10',
        description='排序模式',
        layout=Layout(display='block',width='196px'),
        disabled=False
        )    
    refreshbutton = widgets.Button(description="刷新",layout=Layout(width='48px'))
    needUpdateSlider = True
    needUpdate = True
    def showPlot():
        nonlocal output,category,mark,period,top,sortedCategory,result,bi,ei,pos,needUpdateSlider,periods,cycle,needUpdate,sortType
        if needUpdate:
            if category is None:
                #output.clear_output(wait=True)
                if pos-1>=0:
                    pervSortedCategory = getSortedCategory(period,pos-1)
                else:
                    pervSortedCategory = None
                PlotAllCategory(bi,ei,pos,sortedCategory,pervSortedCategory,top,mark,cycle=cycle,output=output)
            else:
                output.clear_output()
                with output:
                    StrongCategoryCompanyList(result,category,toplevelpos=pos,period=period,periods=periods,cycle=cycle,sortType=sortType)
            needUpdateSlider = True

    def setSlider(minv,maxv,value):
        nonlocal slider,needUpdateSlider
        needUpdateSlider = False
        if minv>slider.max:
            slider.max = maxv
            slider.min = minv
        else:
            slider.min = minv
            slider.max = maxv
        slider.value = value
        listDropdown.value = None

    def on_period(e):
        nonlocal bi,ei,pos,period,category,sortedCategory,LEN
        period = e['new']
        sortedCategory = getSortedCategory(period,pos)
        LEN = len(sortedCategory[0][3])
        bi = LEN-pagecount
        ei = LEN
        pos = LEN-1
        if bi < 0:
            bi = 0
        setSlider(bi,ei,pos)
        listDropdown.value = None
        category = categoryDropdown.value
        categoryDropdown.options = categoryListItem()
        categoryDropdown.value = category
        showPlot()

    periodDropdown.observe(on_period,names='value')  
    
    def on_resverd(e):
        if e['name']=='value':
            nonlocal sortType,needUpdate,sortedCategory,resverdDropdown,mark,category
            needUpdate = False
            sortType = resverdDropdown.value
            sortedCategory = getSortedCategory(period,-1)
            oldmark = mark
            oldcategory = category
            markDropdown.options = markListItem()
            categoryDropdown.options = categoryListItem()
            markDropdown.value = oldmark
            categoryDropdown.value = oldcategory
            needUpdate = True
            showPlot()        
        

    resverdDropdown.observe(on_resverd)
    def on_top(e):
        nonlocal top
        top = e['new']
        listDropdown.value = None
        showPlot()

    topDropdown.observe(on_top,names='value')

    def on_sample(e):
        nonlocal sample
        sample = e['new']
        listDropdown.value = None
        update(True)

    sampleDropdown.observe(on_sample,names='value')
    def on_list(e):
        nonlocal top,pos,category,sortedCategory,cycle
        count = e['new']
        """
        显示TOP分类中的前count只股票
        """
        if count is not None and category is None:
            with output:
                for i in range(top):
                    if i<len(sortedCategory):
                        r = sortedCategory[i]
                        display(Markdown("### %s"%(r[1])))
                        sorti = r[5][:,pos,:]
                        idds = r[4]
                        dd = r[3][pos][0]
                        for j in range(count):
                            if j < len(sorti):
                                inx = int(sorti[j,0])
                                kline.Plote(idds[inx,1],'d',config={'index':True,'markpos':dd},context="强势分类 %s %d"%(r[1],j+1),mode="auto").show(pos=dd)

        else:
            showPlot()

    listDropdown.observe(on_list,names='value')

    def on_mark(e):
        nonlocal mark
        mark = e['new']
        showPlot()

    markDropdown.observe(on_mark,names='value')

    def on_category(e):
        nonlocal category
        if e['name']=='value':
            category = e['new']
            listDropdown.value = None
            showPlot()

    categoryDropdown.observe(on_category,names='value')

    def on_prev(e):
        nonlocal bi,ei,pos,pagecount,LEN
        bi -= pagecount
        if bi<0:
            bi = 0
        ei = bi+pagecount
        if ei>LEN:
            ei = LEN
        pos = ei
        setSlider(bi,ei,pos)
        showPlot()
    def on_next(e):
        nonlocal bi,ei,pos,pagecount,LEN
        ei += pagecount
        if ei>LEN:
            ei = LEN
        bi = ei-pagecount
        if bi<0:
            bi = 0
        pos = ei
        setSlider(bi,ei,pos)
        showPlot()
    def on_zoomin(e):
        nonlocal bi,ei,pagecount,LEN
        if pagecount > 30:
            pagecount -= 10
            bi = ei-pagecount
            if bi<0:
                bi = 0
                ei = bi+pagecount
                if ei>LEN:
                    ei = LEN
            pos = ei
            setSlider(bi,ei,pos)                    
            showPlot()
    def on_zoomout(e):
        nonlocal bi,ei,pos,pagecount,LEN
        if pagecount < 190:
            pagecount += 10
            bi = ei-pagecount
            if bi<0:
                bi = 0
                ei = bi+pagecount
                if ei>LEN:
                    ei = LEN
            pos = ei
            setSlider(bi,ei,pos)                    
            showPlot()
    def on_prevpos(e):
        nonlocal pos,bi,ei,slider,needUpdateSlider,category
        pos -= 1
        if pos<0:
            pos=0
        needUpdateSlider = False
        slider.value = pos
        listDropdown.value = None
        if category is None:
            showPlot()
    def on_nextpos(e):
        nonlocal pos,bi,ei,LEN,slider,needUpdateSlider,category
        pos += 1
        if pos>LEN-1:
            pos=LEN-1
        needUpdateSlider = False
        slider.value = pos
        listDropdown.value = None
        if category is None:
            showPlot()
    def on_sliderChange(e):
        nonlocal period,pos,needUpdateSlider,category,sortedCategory,mark,category,needUpdate
        pos = e['new']
        sortedCategory = getSortedCategory(period,pos)    
        needUpdate = False
        oldMark = mark
        oldCategory = category
        markDropdown.options = markListItem()
        categoryDropdown.options = categoryListItem()
        markDropdown.value = oldMark
        categoryDropdown.value = oldCategory
        needUpdate = True
        if needUpdateSlider and category is None:
            showPlot()
    lock = threading.Lock()
    def update(b):
        lock.acquire()
        nonlocal pos,bi,ei,LEN,result,done,sortedCategory,period,progress,mark,category,needUpdate,sample
        #t0 = datetime.today()
        if b:
            progress = widgets.IntProgress(value=0,
            min=0,max=100,step=1,
            description='download',
            bar_style='',
            orientation='horizontal',layout=Layout(display='flex',
                                flex_flow='wrap',
                                width='100%'))
            with out2:
                display(progress)
            done = False
        else:
            refreshbutton.button_style = 'success'
        progressCallback(0)
        if cycle=='d':
            result = StrongSorted(periods,N,bi=bi,ei=ei,topN=sample,progress=progressCallback,companys=companys)
        elif cycle==5:
            result = StrongSorted5k(periods,N,bi=None,ei=None,topN=sample,progress=progressCallback,companys=companys)
        else: #实时
            result = StrongSortedRT(periods,topN=sample,progress=progressCallback,companys=companys)
        #mylog.info("1."+str(datetime.today()-t0))
        #t0 = datetime.today()
        done = True
        progressCallback(100)
        needUpdate = False
        oldmark = mark
        oldcategory = category
        sortedCategory = getSortedCategory(period,-1)
        markDropdown.options = markListItem()
        categoryDropdown.options = categoryListItem()
        markDropdown.value = oldmark
        categoryDropdown.value = oldcategory
        #mylog.info("2."+str(datetime.today()-t0))
        #t0 = datetime.today()
        LEN = len(sortedCategory[0][3])
        bi = LEN-pagecount
        ei = LEN
        pos = LEN-1
        if bi < 0:
            bi = 0
        setSlider(bi,ei,pos)
        needUpdate = True
        if not b:
            refreshbutton.button_style = ''
        showPlot() 
        lock.release() 
        #mylog.info("3."+str(datetime.today()-t0))
        #t0 = datetime.today()

    def on_refresh(e):
        update(True)

    refreshbutton.on_click(on_refresh)
    prevbutton.on_click(on_prev)
    nextbutton.on_click(on_next)
    zoominbutton.on_click(on_zoomin)
    zoomoutbutton.on_click(on_zoomout)
    backbutton.on_click(on_prevpos)
    frontbutton.on_click(on_nextpos) 
    slider.observe(on_sliderChange,names='value')   
    box_layout = Layout(display='flex',
                    flex_flow='wrap',
                    align_items='stretch',
                    border='solid',
                    width='100%')
    if LEN <= pagecount:
        box = Box(children=[backbutton,slider,frontbutton,periodDropdown,topDropdown,sampleDropdown,listDropdown,resverdDropdown,markDropdown,categoryDropdown,refreshbutton],layout=box_layout)
    else:
        box = Box(children=[prevbutton,nextbutton,zoominbutton,zoomoutbutton,backbutton,slider,frontbutton,periodDropdown,topDropdown,sampleDropdown,listDropdown,resverdDropdown,markDropdown,categoryDropdown,refreshbutton],layout=box_layout)

    display(box,output)
    showPlot() 
    
    lastT = None
    def checkUpdate2():
        nonlocal lastT
        b,t = shared.fromRedis('runtime_update')
        if b and t!=lastT:
            lastT = t
            #update(False)
            threading.Thread(target=update,args=((False,))).start()
        if datetime.today().hour<15:
            xueqiu.Timer(1,checkUpdate2)
    #监视实时数据
    if cycle !='d' and cycle != 5:
        xueqiu.Timer(1,checkUpdate2)
"""
关注
"""
def favoriteList():
    today = date.today()  
    after = today-timedelta(days=20)
    result = stock.query("select * from notebook where date>='%s' order by date desc"%(stock.dateString(after)))
    colles = {}
    out = widgets.Output()
    for it in result:
        if it[1] not in colles:
            colles[it[1]] = []
        colles[it[1]].append(it)
    items = []
    prevButton = None
    for it in colles:
        but = widgets.Button(
                    description=str(it),
                    disabled=False,
                    button_style='')
        but.it = it
        def on_click(e):
            nonlocal prevButton,colles
            if prevButton is not None:
                prevButton.button_style=''
            e.button_style='warning'
            prevButton = e
            f = colles[e.it]
            out.clear_output(wait=True)
            with out:
                for i in f:
                    kline.Plote(i[2].upper(),'d',config={'index':True,'markpos':i[1]},prefix="%s %s "%(i[4],i[5]),context='关注',mode='auto').show()
                    
        but.on_click(on_click)
        items.append(but)
    box = Box(children=items,layout=Layout(display='flex',
            flex_flow='wrap',
            align_items='stretch',
            border='solid',
            width='100%'))    
    display(box,out)

def timeline(code,name=None,companys=None):
    if companys is None:
        companys = stock.query("select company_id,code,name,category from company_select")
    def progress(i):
        pass
    for i in range(len(companys)):
        if companys[i][1]==code or companys[i][2]==name:
            K,D = updateRT(companys,progress=progress)
            gs_kw = dict(width_ratios=[1], height_ratios=[2,1])
            fig,axs = plt.subplots(2,1,sharex=True,figsize=(28,14),gridspec_kw = gs_kw)
            fig.subplots_adjust(hspace=0.02,wspace=0.05)
            axs[0].xaxis.set_major_formatter(MyFormatterRT(D))
            axs[0].set_title("%s %s"%(companys[i][2],companys[i][1]))
            xdd = np.arange(len(D))
            axs[0].plot(xdd,K[i,:,6])
            axs[0].grid(True)
            vol = np.empty(len(D))
            vol[0] = 0#K[i,0,2]
            vol[1:] = K[i,1:,2]-K[i,:-1,2]
            axs[1].bar(xdd,K[i,:,2])
            axs[1].grid(True)
            fig.autofmt_xdate()
            plt.show()
            break