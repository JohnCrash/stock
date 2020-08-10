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

log = mylog.init('status.log',name='status')
class MyFormatterRT(Formatter):
    def __init__(self, dates,fmt='m:s'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0 or math.ceil(x)!=math.floor(x):
            return ''

        t = self.dates[ind][0]
        if self.fmt=='m:s':
            return '%d %02d:%02d:%02d'%(t.day,t.hour,t.minute,t.second)
        else:
            return '%d %02d:%02d'%(t.day,t.hour,t.minute)

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
def insert_company_status(k,macd,vma20,energy,volumeJ,boll,bollw,rsi,idd):
    if len(k)>0:
        qs = ""
        for i in range(len(k)):
            #id , date , close , volume , volumema20 , macd , energy , voluemJ , bollup , bollmid, bolldn , bollw
            try:
                #macd = 0 if k[i][3] is None else k[i][3]
                if i!=len(k)-1:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f),"""%(k[i][0],stock.dateString(idd[i]),k[i][2],k[i][1],vma20[i],macd[i],energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i],rsi[i])
                else:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f)"""%(k[i][0],stock.dateString(idd[i]),k[i][2],k[i][1],vma20[i],macd[i],energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i],rsi[i])
            except Exception as e:
                print(e)
                print(k[i])
                print(idd[i])
        stock.execute("insert ignore into company_status values %s"%(qs))

#bi是更新点-1插入全部
def update_company_status_week(cid,k,macd,vma20,energy,volumeJ,boll,bollw,rsi,idd,bi):
    if len(k)>0:
        #下面更新接头部分的值
        i = bi
        if bi>0:
            qs = "update company_status_week set close=%f,volume=%f,macd=%f,volumema20=%f,energy=%f,volumeJ=%f,bollup=%f,bollmid=%f,bolldn=%f,bollw=%f,rsi=%f where id=%d and date='%s'"%\
            (k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i],ris[i],cid,stock.dateString(idd[i][0]))
            stock.execute(qs)

        #下面是插入新的值
        if bi+1<len(k):
            qs = ""
            for i in range(bi+1,len(k)):
                #id , date , close , volume , macd , volumema20 , energy , voluemJ, bollup , bollmid, bolldn , bollw , rsi
                #k0 volume,1 open,2 high,3 low,4 close
                if i!=len(k)-1:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f),"""%(cid,stock.dateString(idd[i][0]),k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i],rsi[i])
                else:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f)"""%(cid,stock.dateString(idd[i][0]),k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i],boll[i,2],boll[i,1],boll[i,0],bollw[i],rsi[i])
            stock.execute("insert ignore into company_status_week values %s"%(qs))

#依据完整数据更新
def update_company_status_all_data(idk,idd):
    k = np.array(idk)
    #k= [0 id,1 volume,2 close]
    macd = stock.macdV(k[:,2])
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]
    boll = stock.boll(k[:,2])
    bollw = stock.bollWidth(boll)
    rsi = stock.rsi(k[:,2])
    insert_company_status(k,macd,vma20,energy,volumeJ,boll,bollw,rsi,idd)

#依据增量数据更新
def update_company_status_delta_data(idk,idd):
    k = np.array(idk)
    #k= [0 id,1 volume,2 close]
    macd = stock.macdV(k[:,2])
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]
    boll = stock.boll(k[:,2])
    bollw = stock.bollWidth(boll)
    rsi = stock.rsi(k[:,2])
    if len(k)>PROD:
        insert_company_status(k[PROD+1:],macd[PROD+1:],vma20[PROD+1:],energy[PROD+1:],volumeJ[PROD+1:],boll[PROD+1:],bollw[PROD+1:],rsi[PROD+1:],idd[PROD+1:])
    else:
        insert_company_status(k,macd,vma20,energy,volumeJ,boll,bollw,rsi,idd)

#可以从一个起点日期使用增量进行更新，或者更新全部数据
def update_status_begin(beginday,isall,progress):
    if isall:
        rs = stock.query("""select id,date,volume,close from kd_xueqiu where date>'%s'"""%(beginday))
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

        rs = stock.query("""select id,date,volume,close from kd_xueqiu where date>='%s'"""%(lastday))
    idk = {}
    idd = {}
    for i in range(len(rs)):
        d = rs[i]
        key = d[0]
        if key not in idk:
            idk[key] = []
            idd[key] = []
        #0 id,2 volume,3 close
        idk[key].append([rs[i][0],rs[i][2],rs[i][3]])
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
        rsi = stock.rsi(WK[:,4])
        #将周数据更新到company_status_week表中
        #相等部分更新，后面部分插入
        update_company_status_week(key,WK,macd,volumema20,energy,volumeJ,boll,bollw,rsi,wd,bi)
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
        cs=stock.query("""select id,close,volume,volumema20,macd,energy,volumeJ,bollup,bollmid,bolldn,bollw,rsi from %s where date>='%s' and date<='%s'"""%(db,stock.dateString(d[0][0]),stock.dateString(d[-1][0])))
        r = stock.query("""select count(*) from company""")
        n = r[0][0] #公司数量
        dn = len(d)
        a = np.ones((n,dn,12))
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

"""
K_=[[[0 idd,1 timestamp,2 volume,3 current,4 yesteryday_close,5 today_open]
K =[[[(0 idd,1 volume,2 current,3 yesteryday_close,4 today_open)]]]
"""
def downloadAllKFast(companys,step=1,progress=None):
    K_,D_ = xueqiu.getRT(companys,step=step,progress=progress)
    if K_ is not None:
        D = D_
        K = np.ones((len(companys),len(D),11))
        K[:,:,0] = K_[:,:,0] #id
        K[:,:,1] = K_[:,:,2] #volume
        K[:,:,2] = K_[:,:,3] #current
        K[:,:,3] = K_[:,:,4] #yesteryday_close
        K[:,:,4] = K_[:,:,5] #today_open
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
            A = np.vstack((k,[[idd,k1[4],k1[0],0,0,0,0,0,0,0,0,0]]))
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
            A[-1,11] = stock.rsi(A[:,1])[-1] #rsi
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

"""
输入：
tasks[0] = [0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw]...
tasks[1] = [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]...
返回的形式和输入一样，只不过是将当前的数据进行了补全
return [[0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw,11 rsi]...,
        [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]...]
"""
def downloadRT(tasks,progress=None):
    result = []
    if progress is not None:
        progress(0)

    p1,t = xueqiu.lastRT()
    if p1 is not None:
        tv = get_tvol(t)
        idd2inx = {}
        for i in range(len(p1)):
            idd2inx[p1[i,0]] = i
        count = 0
        for it in tasks:
            if it[1][0] in idd2inx:
                i = idd2inx[it[1][0]]
                k = it[0]

                vol = p1[i,2]/tv #使用今天的量仅仅使用分布来推测全天的量
                if vol>10*k[-1,2]: #别太大
                    vol = 10*k[-1,2]
                elif vol<=0:
                    vol = k[-1,2]
                clos = p1[i,3]
                A = np.vstack((k,[[it[1][0],clos,vol,0,0,0,0,0,0,0,0,0]]))
                #0 id ,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw,11 rsi
                A[-1,4] = stock.macdV(A[:,1])[-1] #macd
                A[-1,5] = stock.kdj(stock.volumeEnergy(A[:,2]))[-1,2] #energy
                A[-1,6] = stock.kdj(A[:,2])[-1,2] #volumeJ
                boll = stock.boll(A[:,1])
                bo = boll[-1] #boll
                A[-1,7] = bo[2] #bollup
                A[-1,8] = bo[1] #bollmid
                A[-1,9] = bo[0] #bolldn
                A[-1,10] = stock.bollWidth(boll)[-1] #bollw
                A[-1,11] = stock.rsi(A[:,1])[-1] #rsi
                k = A    
                result.append((k,it[1]))
                if progress is not None:
                    progress(count/len(tasks))
                count+=1 
    if progress is not None:
        progress(100)        
    return result

_id2companys_ = None
_companys_ = None
def get_id2companys():
    global _id2companys_,_companys_
    if _id2companys_ is None:
        _companys_ = stock.query("""select company_id,code,name,category,ttm,pb from company_select""")
        _id2companys_ = {}
        for c in _companys_:
            _id2companys_[c[0]] = c
    return _id2companys_,_companys_

"""
search回调macd能量线双崛起 
a = [[0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw,11 rsi],..]
c = [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]
d = [[date],...]
"""
def cb_macd_energy_buy(a,c,d=None):
    dMACD = a[-1,4]-a[-2,4]
    #macd在零轴附件（预计2日穿过或者已经穿过2日）,股价涨,能量线崛起
    if dMACD>0 and a[-1,1]-a[-2,1]>0 and a[-1,5]>=3 and a[-2,5]<3:
        if (a[-1,4]<0 and a[-1,4]+2*dMACD>0) or (a[-1,4]>0 and a[-1,4]-2*dMACD<0):
            return True
    return False

def cb_rsi_left_buy(a,c,d=None):
    return a[-1,11]<=20

def cb_rsi_left_sell(a,c,d=None):
    return a[-1,11]>=80

def cb_volumeJ_left_buy(a,c,d=None):
    return a[-1,6]<=5

def cb_volumeJ_left_sell(a,c,d=None):
    return a[-1,6]>=95

def cb_rsi_right_buy(a,c,d=None):
    return a[-2,11]<=20 and a[-1,11]>20

def cb_rsi_right_buy20_30(a,c,d=None):
    return a[-2,11]<=30 and a[-1,11]>30

def cb_rsi_right_sell(a,c,d=None):
    return a[-2,11]>=80 and a[-1,11]<80

def cb_volumeJ_right_buy(a,c,d=None):
    return a[-2,6]<=5 and a[-1,6]>5

def cb_volumeJ_right_sell(a,c,d=None):
    return a[-2,6]>=95 and a[-1,6]<95

#boll通道窄2.0以下，持续30以上(不算最近一天)
def cb_bollwidth(a,c,d=None):
    for i in range(-30,-1):
        if a[i,10]>0.2:
            return False
    return True
#boll通道窄2.0以下，持续20以上
def cb_bollwidth15(a,c,d=None):
    for i in range(-30,-1):
        if a[i,10]>0.15:
            return False
    return True    
#boll通道上方附近（大于中线到boll顶2/3处）
def cb_boll_up(a,c,d=None):
    return a[-1,1]>(a[-1,8]+(a[-1,7]-a[-1,8])*2/3)
#boll通道下方附近
def cb_boll_down(a,c,d=None):
    return a[-1,1]<(a[-1,9]+(a[-1,8]-a[-1,9])/3)
#成交量放出巨量当日
def cb_volume_huge(a,c,d=None):
    return a[-1,2]>2*a[-2,2] and a[-1,1]>a[-2,1]
#成交量持续放大，股价持续上涨
def cb_volume_price_grow(a,c,d=None):
    return a[-1,2]>a[-2,2] and a[-2,2]>a[-3,2] and a[-1,1]>a[-3,1]
"""
搜索符合条件的股票
method(k,c,d) 搜索方法
k [0 id ,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw,11 rsi]
c [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]
d [date]
返回按分类符合条件的集合
{category:[[0 company_id,1 code,2 name,3 category,4 ttm,5 pb],]}
"""
def search(method,category=None):
    d,a = redisStatusCache50('company_status')
    id2companys,_ = get_id2companys()
    tasks = []
    results = []
    isNotDownloadK = date.today()!=d[-1][0]
    if stock.isTransTime() or isNotDownloadK:
        dd = d+[(date.today(),)]
    else:
        dd = d
    for i in range(len(a)):
        c = a[i]
        idd = int(c[-1][0])
        #反转数组的前后顺序，反转后-1代表最近的数据
        k = c#0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw,11 rsi
        if idd in id2companys and (category is None or id2companys[idd][3]==category):
            if stock.isTransTime() or isNotDownloadK: #将当日数据叠加进数据中
                tasks.append((k,id2companys[idd]))
            else:
                results.append((k,id2companys[idd]))

    if len(tasks)>0:
        results = downloadRT(tasks)                
    r = {}
    for it in results:
        b = method(it[0],it[1],dd)
        if b:
            if it[1][3] not in r:
                r[it[1][3]] = []
            r[it[1][3]].append(it[1])
    return r     
"""
dd = 最后一个数据的时间点
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
    isNeedDownload = False
    bi = len(d)-1
    for i in range(len(d)):
        if str(d[i][0])==dd:
            bi = i
    if date.today()==date.fromisoformat(dd):
        istoday = True
    #如果Cache50中的数据不包括当天数据，并且当天是一个交易日，则需要下载新的数据
    if stock.isTransDay() and d[-1][0] != date.fromisoformat(dd):
        isNeedDownload = True

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
            if istoday and isNeedDownload and period=='d': #将当日数据叠加进数据中
                tasks.append((k,id2companys[idd]))
            else:
                results.append((k,id2companys[idd]))
    
    progress(40)
    def progress40_90(i):
        if math.floor(i)%5==0:
            progress(i/2+40)
    if len(tasks)>0:
        results = downloadRT(tasks,progress40_90)
    progress(90)
    for it in results:
        b,vline = cb(it[0],it[1])
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
            if istoday and stock.isTransTime() and period=='d': #将当日数据叠加进数据中
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
def searchRasingCompanyStatusByRedisRange(bi,ei,dd,period,cb,id2companys,progress):
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
        if idd in id2companys:
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
def SearchRT(period='d',cb=None,name=None,bi=None,ei=None):
    today_but = None
    cbs = [None,None,None]
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
    id2companys,companys = get_id2companys()
    if bi is not None:
        dates = stock.query("select date from %s where id=8828 and date>='%s' and date<='%s' order by date desc"%('company_status' if period=='d' else 'company_status_week',bi,ei))
    else:
        dates = stock.query('select date from %s where id=8828 order by date desc limit 50'%('company_status' if period=='d' else 'company_status_week'))
    
    prevClickButton = None
    prevClickButtonStyle = None
    #点击日期
    def onCatsList(E):
        nonlocal progress,prevClickButton,prevClickButtonStyle,cbs
        def combo_cb(*args):
            r = False
            ls = []
            for cb in cbs:
                if cb is not None:
                    b,ls = cb(*args)
                    if b:
                        r = b
                    else:
                        return False,[]
            return r,ls
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
            rasing,vlines = searchRasingCompanyStatusByRT(E.date,period,combo_cb,id2companys,progressCallback)
        else:
            rasing,vlines = searchRasingCompanyStatusByRedisRange(bi,ei,E.date,period,combo_cb,id2companys,progressCallback)
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
    methodlists = ['双崛起买点','RSI左买点','RSI右买点(<20)','RSI右买点(20-30)','volumeJ左买点',
                    'volumeJ右买点','bollwidth<0.2(30)','bollwidth<0.15(30)','boll通道顶','boll通道底部',
                    '成交量显著放大','量价齐升']
    methodDropdown = widgets.Dropdown(
        options=methodlists+(['自定义'] if cb is not None else []),
        value='自定义' if cb is not None else '双崛起买点',
        description='搜索算法',
        layout=Layout(display='block',width='296px'),
        disabled=False)
    methodDropdown1 = widgets.Dropdown(
        options=['None']+methodlists,
        value='None',
        description='&&',
        layout=Layout(display='block',width='296px'),
        disabled=False)
    methodDropdown2 = widgets.Dropdown(
        options=['None']+methodlists,
        value='None',
        description='&&',
        layout=Layout(display='block',width='296px'),
        disabled=False)
    def wrap(func):
        def ccb(a,c):
            if func(a,c):
                return True,[{'x':[-1],'color':'magenta','linestyle':'--','linewidth':2}]
            else:
                return False,[]
        return ccb
    def selectMethod(sel,i):
        nonlocal cbs,cb
        if sel=='双崛起买点':
            cbs[i] = wrap(cb_macd_energy_buy)
        elif sel=='RSI左买点':
            cbs[i] = wrap(cb_rsi_left_buy)
        elif sel=='RSI右买点(<20)':
            cbs[i] = wrap(cb_rsi_right_buy)
        elif sel=='RSI右买点(20-30)':
            cbs[i] = wrap(cb_rsi_right_buy20_30)
        elif sel=='volumeJ左买点':
            cbs[i] = wrap(cb_volumeJ_left_buy)
        elif sel=='volumeJ右买点':
            cbs[i] = wrap(cb_volumeJ_right_buy)
        elif sel=='bollwidth<0.2(30)':
            cbs[i] = wrap(cb_bollwidth)
        elif sel=='bollwidth<0.15(30)':
            cbs[i] = wrap(cb_bollwidth15)
        elif sel=='boll通道顶':
            cbs[i] = wrap(cb_boll_up)
        elif sel=='boll通道底部':
            cbs[i] = wrap(cb_boll_down)    
        elif sel=='成交量显著放大':
            cbs[i] = wrap(cb_volume_huge) 
        elif sel=='量价齐升':                      
            cbs[i] = wrap(cb_volume_price_grow)            
        elif sel=='自定义':
            cbs[0] = cb
        elif sel=='None':
            cbs[i] = None
    selectMethod(methodDropdown.value,0)
    selectMethod(methodDropdown1.value,1)
    selectMethod(methodDropdown1.value,2)
    def on_selectmethod(e):
        sel = e['new']
        selectMethod(sel,0)
    def on_selectmethod1(e):
        sel = e['new']
        selectMethod(sel,1)
    def on_selectmethod2(e):
        sel = e['new']
        selectMethod(sel,2)
    methodDropdown.observe(on_selectmethod,names='value')
    methodDropdown1.observe(on_selectmethod1,names='value')
    methodDropdown1.observe(on_selectmethod2,names='value')
    box = Box(children=items, layout=box_layout)
    toolbox = Box(children=[methodDropdown,methodDropdown1,methodDropdown2], layout=box_layout)
    display(toolbox,box,output)

    def updatek15():
        nonlocal today_but
        if stock.isTransTime():
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
     8 该分类成交量占比变化率[date_n]
     9 该分类成交量占比[date_n]
     )
]
K = [company_n,date_n,(0 idd,1 volume,2 close,3 yesteryday_close,4 today_open)]
D = [(date,)...]
#使用线程加速 ,单线程更快，测试结果多线程用时4s,单线程用2s
"""
def processKD2_CB(K,D,companys,topN=20): #对processKD2的优化，只有在需要的时候才处理数据
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
    result = []
    result_passed = {}
    """
    day = int 周期（和多少个周期前比较增长）
    day = 'd' 周期盈利将变成日盈利(和昨日收盘进行比较)
    day = 's' 通过和大盘的上涨和下跌周期来计算
    """
    def calcCB(day):
        if day=='s':
            return calcStrongCB()
        else:
            return calcDayCB(day)
    def calcStrongCB():
        nonlocal idd,id2com,result,K,D,topN,result_passed
        
    def calcDayCB(day):
        nonlocal idd,id2com,result,K,D,topN,result_passed
        
        if day in result_passed:
            return result
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
        S = np.sum(K[:,:,1],axis=0)
        for category in allCategory():
            r = idd[:,3]==category
            dK = dk[r]
            vK = np.sum(K[r,:,1],axis=0)/S #分类占比
            ma5 = stock.ma(vK,5)
            if day=='d':
                vdK = vK #分类占比
            else:
                vdK = vK[day:]/ma5[:-day]-1 #分类占比变化
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
                    result.append((day,category,dK,D[:],idd[r],sorti,top10mean,low10mean,vdK,vdK))
                else:
                    result.append((day,category,dK,D[day:],idd[r],sorti,top10mean,low10mean,vdK,vK[day:]))
            else:
                print("'%s' 分类里面没有公司"%category)
        result_passed[day] = True
        return result
    
    return calcCB

def StrongSorted(N=50,bi=None,ei=None,topN=20,progress=None,companys=None):
    K_ = None
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
        b,t = xueqiu.getLastUpdateTimestamp()
        today = datetime.today()
        if b and t.month==today.month and t.day==today.day and D[-1][0].day!=t.day: #有新的数据,将最新的数据叠加进去
            p,_ = xueqiu.lastRT()
            if p is not None:
                K_ = np.zeros((len(K),len(D)+1,5))
                K_[:,:-1,0] = K[:,:,0]
                K_[:,:-1,1] = K[:,:,2]
                K_[:,:-1,2] = K[:,:,1]
                idd2inx = {}
                for i in range(len(p)):
                    idd2inx[int(p[i,0])] = i
                for i in range(len(K)):
                    idd = int(K_[i,-2,0])
                    if idd in idd2inx:
                        K_[i,-1,0] = idd
                        K_[i,-1,1] = p[idd2inx[idd],2]
                        clos = p[idd2inx[idd],3]
                        if clos>0 and K_[i,-1,2]>0:
                            v = clos/K_[i,-1,2]
                            if v<=1.1 and v>=0.9:
                                K_[i,-1,2] = p[idd2inx[idd],3]
                            else:
                                K_[i,-1,2] = K_[i,-2,2]
                        else:
                            K_[i,-1,2] = K_[i,-2,2]
                dd = date.fromtimestamp(seqs[-1]/(1000*1000))
                D.append((dd,))
    # K = [(0 idd,1 close,2 volume,3 volumema20,4 macd,5 energy,6 volumeJ,7 bollup,8 bollmid,9 bolldn,10 bollw)]
    # K_ = [(0 idd,1 volume,2 close,3 yesteryday_close,4 today_open)]
    if K_ is None:
        K_ = np.zeros((len(K),len(D),5))
        K_[:,:,0] = K[:,:,0]
        K_[:,:,1] = K[:,:,2]
        K_[:,:,2] = K[:,:,1]
    #舍弃3 yesteryday_close,4 today_open
    return processKD2_CB(K_,D,companys,topN=topN)
  
def StrongSorted5k(N=50,bi=None,ei=None,topN=20,progress=None,companys=None):
    progress(0)
    D,K = loadAllK(companys,bi,ei,5,N,progress)
    progress(100)
    if D is None or K is None:
        return []
    return processKD2_CB(K,D,companys,topN=topN)

def StrongSortedRT(topN=20,step=1,progress=None,companys=None):
    progress(0)
    D,K = downloadAllKFast(companys,step,progress)
    if D is None or K is None:
        return []
    result = processKD2_CB(K,D,companys,topN=topN)    
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
def StrongCategoryCompanyList(category,name,toplevelpos=None,period=20,periods=[3,5,10,20],cycle='d',sortType='TOP10',result_cb=None):
    def getResult(day,categoryName):
        nonlocal category
        category = result_cb(day)
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
                kline.Plote(getCodeByName(com),'d',config={'index':True,'markpos':dd},context="强势分类 %s"%(name),mode="runtime").show()

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

def PlotAllCategory(period,bi,ei,pos,sortedCategory,pervSortedCategory,top,focus=None,cycle='d',output=None):
    fig,axs = plt.subplots(1 if period=='d' else 2,1,figsize=(28,16),sharex=True)
    fig.subplots_adjust(hspace=0.0,wspace=0.00) #调整子图上下间距
    r = sortedCategory[0]
    dd = r[3] #date
    if pos>=len(dd):
        pos = len(dd)-1
    axs0 = axs[0] if type(period)==int else axs
    if cycle=='d' or cycle==5:
        axs0.xaxis.set_major_formatter(kline.MyFormatter(dd,cycle))
    else:
        axs0.xaxis.set_major_formatter(MyFormatterRT(dd,cycle))
    if top is None:
        axs0.set_title("%s 周期%s"%(r[1],r[0]))
    else:
        axs0.set_title("%s 周期%s Top%s"%(r[1],r[0],top))
    
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
    def mapLineWidth(v):
        lw = v/0.005
        return lw if lw>0.5 else 0.5
    #曲线的提示文字，将图像分成3个部分，每个部分的前3名将被标注
    vti = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,.9,1]
    vts = np.zeros((len(vti),top))
    vts2 = np.zeros((len(vti),top))
    for i in range(len(sortedCategory)):
        r = sortedCategory[i]
        color = getmycolor(r[1])
        dk = r[6] #
        vk = r[8] #成交量占比变化
        if i<top:
            for p in range(len(vti)):
                x = math.floor(bi+(ei-bi-1)*vti[p])
                vts[p,i] = dk[x]
                vts2[p,i] = vk[x]
        lw = mapLineWidth(r[9][pos]) #成交量占比,变换为线宽
        if pervSortedCategory is None:
            title = "%d %s"%(i+1,r[1])
        else:
            title = "%d %s %s"%(i+1,r[1],getPrevRank(r[1],i))
        if top is not None:
            if i<top:
                if focus is not None:
                    if isFocusIt(focus,r[1],i,top):
                        axs0.plot(xdd[bi:ei],dk[bi:ei],linewidth=lw,label = title,color=color)
                        if type(period)==int:
                            axs[1].plot(xdd[bi:ei],vk[bi:ei],linewidth=lw,label = title,color=color)
                    else:
                        axs0.plot(xdd[bi:ei],dk[bi:ei],alpha=0.2,linewidth=lw,label = title,color=color)
                        if type(period)==int:
                            axs[1].plot(xdd[bi:ei],vk[bi:ei],alpha=0.2,linewidth=lw,label = title,color=color)
                else:        
                    axs0.plot(xdd[bi:ei],dk[bi:ei],linewidth=lw,label = title,color=color)
                    if type(period)==int:
                        axs[1].plot(xdd[bi:ei],vk[bi:ei],linewidth=lw,label = title,color=color)
            else:
                if focus is not None and isFocusIt(focus,r[1],i,top):
                    axs0.plot(xdd[bi:ei],dk[bi:ei],linewidth=lw,linestyle='--',label = title,color=color)
                    if type(period)==int:
                        axs[1].plot(xdd[bi:ei],vk[bi:ei],linewidth=lw,linestyle='--',label = title,color=color)

    #绘制标记文本
    vvts = np.argsort(vts,axis=1)
    vvts2 = np.argsort(vts2,axis=1)
    isin = []
    isin2 = []
    for p in range(len(vti)-1,-1,-1):
        x = math.floor(bi+(ei-bi-1)*vti[p])
        for i in (-1,-2):
            y = vts[p,vvts[p,i]]
            y2 = vts2[p,vvts2[p,i]]
            r = sortedCategory[int(vvts[p,i])]
            r2 = sortedCategory[int(vvts2[p,i])]
            s = r[1]
            s2 = r2[1]
            color = getmycolor(s)
            color2 = getmycolor(s2)
            tx = -30+i*20
            ty = 50+i*10
            if s not in isin:
                isin.append(s)
                axs0.annotate(s,xy=(x,y),xytext=(tx, ty), textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",
                        connectionstyle="angle,angleA=0,angleB=90,rad=10"),color=color,fontsize='large')
            if s2 not in isin2:
                isin2.append(s2)
                if type(period)==int:
                    axs[1].annotate(s2,xy=(x,y2),xytext=(tx, ty), textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",
                            connectionstyle="angle,angleA=0,angleB=90,rad=10"),color=color2,fontsize='large')

    axs0.axvline(pos,color="red",linewidth=2,linestyle='--')
    if type(period)==int:
        axs[1].axvline(pos,color="red",linewidth=2,linestyle='--')
    xticks=[]
    for i in range(bi,ei):
        xticks.append(i)
    xticks.append(pos)
    axs0.set_xticks(xticks)
    axs0.grid(True)
    axs0.axhline(0,color='black',linewidth=1,linestyle='--')
    axs0.set_xlim(bi,ei-1)
    if type(period)==int:
        axs[1].grid(True)
        axs[1].axhline(0,color='black',linewidth=1,linestyle='--')
        plt.legend(bbox_to_anchor=(1, 2),loc='upper left',fontsize='large')
    else:
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
def StrongCategoryList(N=50,cycle='d',step=1,bi=None,ei=None):
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
        result_cb = StrongSorted(N,bi=bi,ei=ei,topN=sample,progress=progressCallback,companys=companys)
    elif cycle==5:
        periods = [1,3,6,9,12,15]
        period = 3
        result_cb = StrongSorted5k(N,bi=bi,ei=ei,topN=sample,progress=progressCallback,companys=companys)
    else: #实时
        periods = [3,15,45,'d']
        period = 15
        result_cb = StrongSortedRT(topN=sample,step=step,progress=progressCallback,companys=companys)
    result = result_cb(period)

    done = True
    sortType = '涨幅榜'
    progressCallback(100)
    output = widgets.Output()
    def getSortedCategory(day,pos):
        nonlocal sortType,result_cb,result
        categorys = []
        result = result_cb(day)
        if len(result)==0:
            return []
        for r in result:
            if r[0]==day:
                categorys.append(r)
        if pos > len(categorys[0][6])-1:
            pos = len(categorys[0][6])-1
        if pos < -len(categorys[0][6]):
            pos = -len(categorys[0][6])                
        if sortType=='涨幅榜':
            return sorted(categorys,key=lambda it:it[6][pos],reverse=True)
        elif sortType=='跌幅榜':
            return sorted(categorys,key=lambda it:it[7][pos])
    
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
        options=['涨幅榜','跌幅榜'],
        value='涨幅榜',
        description='排序模式',
        layout=Layout(display='block',width='196px'),
        disabled=False
        )    
    refreshbutton = widgets.Button(description="刷新",layout=Layout(width='48px'))
    needUpdateSlider = True
    needUpdate = True
    def showPlot():
        nonlocal output,category,mark,period,top,sortedCategory,result,bi,ei,pos,needUpdateSlider,periods,cycle,needUpdate,sortType,result_cb
        if needUpdate:
            if category is None:
                #output.clear_output(wait=True)
                if pos-1>=0:
                    pervSortedCategory = getSortedCategory(period,pos-1)
                else:
                    pervSortedCategory = None
                PlotAllCategory(period,bi,ei,pos,sortedCategory,pervSortedCategory,top,mark,cycle=cycle,output=output)
            else:
                output.clear_output()
                with output:
                    StrongCategoryCompanyList(result,category,toplevelpos=pos,period=period,periods=periods,cycle=cycle,sortType=sortType,result_cb=result_cb)
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
        nonlocal bi,ei,pos,period,category,sortedCategory,LEN,result_cb,result,step

        if period!='d' and e['new']=='d': #重新获取数据
            step = 15
            period = e['new']
            update(True)
        elif e['new']!='d' and period=='d':
            step = 1
            period = e['new']
            update(True)
        else:
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
                                kline.Plote(idds[inx,1],'d',config={'index':True,'markpos':dd},context="强势分类 %s %d"%(r[1],j+1),mode="runtime").show(pos=dd)

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
        nonlocal pos,bi,ei,LEN,result,done,sortedCategory,period,progress,mark,category,needUpdate,sample,result_cb,step
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
            result_cb = StrongSorted(N,bi=bi,ei=ei,topN=sample,progress=progressCallback,companys=companys)
        elif cycle==5:
            result_cb = StrongSorted5k(N,bi=bi,ei=ei,topN=sample,progress=progressCallback,companys=companys)
        else: #实时
            result_cb = StrongSortedRT(topN=sample,step=step,progress=progressCallback,companys=companys)
        result = result_cb(period)
        #log.info("1."+str(datetime.today()-t0))
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
        #log.info("2."+str(datetime.today()-t0))
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
        #log.info("3."+str(datetime.today()-t0))
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
        b,t = xueqiu.getLastUpdateTimestamp()
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
                    description="%s (%d)"%(str(it),len(colles[it])),
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

def timeline(code,step=1,name=None,companys=None):
    if companys is None:
        companys = stock.query("select company_id,code,name,category from company_select")
    for i in range(len(companys)):
        if companys[i][1]==code or companys[i][2]==name:
            K,D = xueqiu.getRT(companys,step=step)
            gs_kw = dict(width_ratios=[1], height_ratios=[2,1])
            fig,axs = plt.subplots(2,1,sharex=True,figsize=(28,14),gridspec_kw = gs_kw)
            fig.subplots_adjust(hspace=0.02,wspace=0.05)
            axs[0].xaxis.set_major_formatter(MyFormatterRT(D))
            axs[0].set_title("%s %s"%(companys[i][2],companys[i][1]))
            xdd = np.arange(len(D))
            axs[0].plot(xdd,K[i,:,3])
            axs[0].grid(True)
            vol = np.empty(len(D))
            vol[0] = 0#K[i,0,2]
            vol[1:] = K[i,1:,2]-K[i,:-1,2]
            #axs[1].bar(xdd,K[i,:,2])
            axs[1].bar(xdd,vol)
            axs[1].grid(True)
            fig.autofmt_xdate()
            plt.show()
            break
#交易结束保存资金流向数据
def saveflow(name=None):
    if name==None:
        t = datetime.today()
        name = "flow_%d_%d"%(t.month,t.day)     
    b,a = shared.fromRedis(name)
    if b:
        sqlstr = None
        for v in a:
            if sqlstr is None:
                sqlstr = "('%s',%f,%f,%f,%f)"%(stock.timeString(v[0]),v[1],v[2],v[3],v[4])
            else:
                sqlstr += ",('%s',%f,%f,%f,%f)"%(stock.timeString(v[0]),v[1],v[2],v[3],v[4])
        stock.execute("insert ignore into flow (date,larg,big,mid,tiny) values %s"%sqlstr)

#如果某一天没有数据,可以使用历史上比较接近的一天进行替换
def saveflow2(today,history):
    history2 = stock.dateString(date.fromisoformat(history)+timedelta(days=1))
    flow = stock.query("select date,larg,big,mid,tiny from flow where date>'%s' and date<'%s'"%(history,history2))
    sqlstr = None
    for v in flow:
        t = v[0]
        dd = "%s %s:%s:%s"%(today,t.hour,t.minute,t.second)
        if sqlstr is None:
            sqlstr = "('%s',%f,%f,%f,%f)"%(dd,v[1],v[2],v[3],v[4])
        else:
            sqlstr += ",('%s',%f,%f,%f,%f)"%(dd,v[1],v[2],v[3],v[4])
    stock.execute("insert ignore into flow (date,larg,big,mid,tiny) values %s"%sqlstr)
#显示资金流向
def showflow(name=None):
    if name==None:
        t = datetime.today()
        n=0
        while n<5:
            name = "flow_%d_%d"%(t.month,t.day)
            b,a = shared.fromRedis(name)
            if b:
                break
            else:
                t = t-timedelta(days=1)
            n+=1

    output = widgets.Output()
    display(output)
    first = True 
    def plotflow():
        nonlocal output,name
        t = datetime.today()
        n = "flow_%d_%d"%(t.month,t.day)
        b,a = shared.fromRedis(n)
        if not b:
            b,a = shared.fromRedis(name)
        if b:
            fig,axs = plt.subplots(figsize=(28,14))
            axs.set_title("资金流向 %s %s"%(name,str(t)))
            d = np.zeros((len(a),5))
            i = 0
            dd = []
            xticks=[]
            for v in a:
                dd.append([v[0]])
                d[i][0] = i
                d[i][1] = v[1]
                d[i][2] = v[2]
                d[i][3] = v[3]
                d[i][4] = v[4]
                i+=1
            for i in range(4*60):
                if i%10==0:
                    xticks.append(i)
            xticks.append(len(a)-1)
            axs.xaxis.set_major_formatter(MyFormatterRT(dd))
            axs.plot(d[:,0],d[:,1],color="red",label="巨 %d亿"%(d[-1,1]/1e8))
            axs.plot(d[:,0],d[:,2],color="yellow",label="大 %d亿"%(d[-1,2]/1e8))
            axs.plot(d[:,0],d[:,3],color="cyan",label="中 %d亿"%(d[-1,3]/1e8))
            axs.plot(d[:,0],d[:,4],color="purple",label="小 %d亿"%(d[-1,4]/1e8))
            axs.set_xticks(xticks)
            axs.grid(True)
            axs.set_xlim(0,4*60)
            axs.axhline(y=0,color='black',linestyle='--')
            fig.autofmt_xdate()
            axs.legend()
            kline.output_show(output)
    def update():
        nonlocal first
        t = datetime.today()
        if first or stock.isTransTime(t):
            with output:
                plotflow()
        if t.hour>=6 and t.hour<15:
            xueqiu.Timer(60,update) #60秒更新一次
        first = False
    update()

# D=[(timestamp,),...]
# K=(0 idd,1 volume,2 close,3 yesteryday_close,4 today_open)
def getRT2m(companys):
    k,D = xueqiu.getRT(companys,step=6,N=0)
    K = np.empty((len(k),len(D),5))
    K[:,:,0] = k[:,:,0]
    K[:,:,1:] = k[:,:,2:]
    return D,K
"""
显示涨停板数和跌停板数量
bi,ei可以指定数据范围
"""
def showzdt(bi=None,ei=None):
    D = None
    K = None
    hot = None
    listState = False
    method = 'None'
    uhots = []
    dhots = []
    SS = None
    mode = '2分钟'
    companys = stock.query("""select company_id,code,name,category from company_select""")
    id2com = {}
    pos = -1
    bii = -100
    eii = -1
    sel = '全部'
    idd = None
    for com in companys:
        id2com[com[0]] = com
    backbutton = widgets.Button(description="<",layout=Layout(width='48px'))
    frontbutton = widgets.Button(description=">",layout=Layout(width='48px'))
    slider = widgets.IntSlider(
        value=pos,
        min=bii,
        max=eii,
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
        options=['2分钟','日'],
        value=mode,
        description='周期',
        layout=Layout(display='block',width='120px'),
        disabled=False)
    categoryDropdown = widgets.Dropdown(
        options=['全部','涨停热点','跌停热点']+allCategory(),
        value=sel,
        description='选择分类',
        layout=Layout(display='block',width='215px'),
        disabled=False)
    hotsDropdown = widgets.Dropdown(
        options=[],
        value=None,
        description='热点',
        layout=Layout(display='block',width='215px'),
        disabled=False)     
    nextDropdown = widgets.Dropdown(
        options=['None','平均'],
        value=method,
        description='次日',
        layout=Layout(display='block',width='215px'),
        disabled=False)           
    listbutton = widgets.Button(description="选择列表",layout=Layout(width='82px'))         
    refreshbutton = widgets.Button(description="刷新",layout=Layout(width='48px'))           
    output = widgets.Output()
    output2 = widgets.Output()
    output3 = widgets.Output()
    box_layout = Layout(display='flex',
                    flex_flow='wrap',
                    align_items='stretch',
                    border='solid',
                    width='100%')    
    box = Box(children=[backbutton,slider,frontbutton,periodDropdown,categoryDropdown,hotsDropdown,listbutton,nextDropdown,refreshbutton],layout=box_layout)
    def getData():
        nonlocal K,D,mode,companys,uhots,dhots,bi,ei,pos
        if mode == '2分钟':
            D,K = getRT2m(companys)
        else:
            if bi is None:
                D,K_ = redisStatusCache50('company_status')
            else:
                if ei is None:
                    ei=stock.dateString(date.today())
                D,K_ = getStatusN(bi=bi,ei=ei)
            K = np.zeros((len(K_),len(D),5))
            K[:,:,0] = K_[:,:,0]
            K[:,:,1] = K_[:,:,2]
            K[:,:,2] = K_[:,:,1]
            K[:,0,3] = K_[:,0,1]
            K[:,1:,3] = K_[:,:-1,1]
        K[K[:,:,3]<=0] = 1
        #重新计算热点分类
        idd = np.empty((len(K),4),dtype=np.dtype('O')) #(0 id , 1 code , 2 name , 3 category)
        idd[:,0] = K[:,0,0]        
        for i in idd:
            k = int(i[0])
            if k in id2com:
                i[1] = id2com[k][1]
                i[2] = id2com[k][2]
                i[3] = id2com[k][3]            
        r = K[:,pos,2]/K[:,pos,3]-1
        S = []
        for category in allCategory():
            sr = idd[:,3]==category
            u = np.count_nonzero(r[sr]>=0.097)
            d = np.count_nonzero(r[sr]<=-0.097)
            S.append((category,u,d))
        #涨幅榜前10
        um = sorted(S,key=lambda it:it[1],reverse=True)
        uhots = []
        for i in range(10):
            if i < len(um):
                uhots.append(um[i][0])
        #跌幅前10
        dm = sorted(S,key=lambda it:it[2],reverse=True)
        dhots = []
        for i in range(10):
            if i < len(dm):
                dhots.append(dm[i][0])
        hotsDropdown.options = []
        hotsDropdown.value = None

    def on_prevpos(e):
        nonlocal pos,bii,eii,slider
        pos -= 1
        if pos<bii:
            pos=bii
        slider.value = pos
        update_zdt()
    def on_nextpos(e):
        nonlocal pos,bii,eii,slider
        pos += 1
        if pos>-1:
            pos=-1
        slider.value = pos
        update_zdt()
    def on_refresh(e):
        update_zdt()
    def on_sliderChange(e):
        nonlocal pos
        pos = e['new']
        update_zdt()
    def slider_range(b,e):
        nonlocal slider,pos,bii,eii
        bii = b
        eii = e
        slider.max = eii
        slider.min = bii
        slider.pos = pos
    def on_category(e):
        nonlocal sel,uhots,dhots
        if e['name']=='value':
            sel = e['new']
            if sel=='涨停热点':
                hotsDropdown.options = uhots
                hotsDropdown.value = uhots[0]
            elif sel=='跌停热点':
                hotsDropdown.options = dhots
                hotsDropdown.value = dhots[0]
            update_zdt()
    def on_period(e):
        nonlocal mode,pos
        if e['name']=='value':
            mode = e['new']
            pos = -1
            getData()
            update_zdt()
    def on_hots(e):
        nonlocal hot
        if e['name']=='value':
            hot = e['new']
            update_zdt()
    periodDropdown.observe(on_period,names='value')
    categoryDropdown.observe(on_category,names='value')
    hotsDropdown.observe(on_hots,names='value')
    refreshbutton.on_click(on_refresh)
    backbutton.on_click(on_prevpos)
    frontbutton.on_click(on_nextpos)
    slider.observe(on_sliderChange,names='value')   
    display(box,output,output2,output3)
    #涨停板次日
    def on_next(e):
        nonlocal method
        if e['name']=='value':
            method = e['new']
            update_zdt()
    nextDropdown.observe(on_next,names='value')
    def clear_output2():
        nonlocal output2,output3
        output2.clear_output()
        output3.clear_output()
    def on_company(e):
        nonlocal output3
        output3.clear_output(wait=True)
        with output3:
            kline.Plote(e.code,'d',config={'index':True},context="实时涨跌",mode="auto").show()
    def list_output2(names,codes,ums,dms):
        nonlocal box_layout,output2
        children = []
        with output2:
            for i in range(len(names)):
                if ums[i]>0 and dms[i]==0:
                    bs = 'danger'
                elif ums[i]==0 and dms[i]>=0:
                    bs = ''
                else:
                    bs = 'success'             
                but = widgets.Button(
                    description=names[i],
                    disabled=False,
                    button_style=bs,
                    layout=Layout(width='76px')
                    )
                but.code = codes[i]
                but.on_click(on_company)
                children.append(but)
        with output2:
            box = Box(children=children,layout=box_layout)
            display(box)
    def on_category_list(e):
        nonlocal output3
        output3.clear_output(wait=True)
        with output3:
            for c in e.category[3]:
                kline.Plote(c[1],'d',config={'index':True},context="实时涨跌",mode="runtime").show()
    def list_output2_category(categorys):
        nonlocal box_layout,output2
        children = []
        with output2:
            for i in range(len(categorys)):
                if categorys[i][1]>0 and categorys[i][2]==0:
                    bs = 'danger'
                elif categorys[i][1]==0 and categorys[i][2]>=0:
                    bs = 'success'
                else:
                    bs = ''
                but = widgets.Button(
                    description=categorys[i][0],
                    disabled=False,
                    button_style=bs,
                    layout=Layout(width='76px')
                    )
                but.category = categorys[i]
                but.on_click(on_category_list)
                children.append(but)
        with output2:
            box = Box(children=children,layout=box_layout)
            display(box)
    
    def on_list(e):
        nonlocal listState
        if listState:
            listState = False
            e.button_style = ''
        else:
            listState = True
            e.button_style = 'success'
        update_zdt()
    listbutton.on_click(on_list)
    first = True
    def update_zdt():
        nonlocal K,D,output,pos,bii,eii,sel,idd,K,D,mode,uhots,dhots,hot,SS,listState,method

        slider_range(-len(D)+1,-1)

        idd = np.empty((len(K),4),dtype=np.dtype('O')) #(0 id , 1 code , 2 name , 3 category)
        idd[:,0] = K[:,0,0]        
        for i in idd:
            k = int(i[0])
            if k in id2com:
                i[1] = id2com[k][1]
                i[2] = id2com[k][2]
                i[3] = id2com[k][3]           
        fig,axs = plt.subplots(2,1,figsize=(30,14),sharex=False if method=='None' else True)
        fig.subplots_adjust(hspace=0.1,wspace=0.05) #调整子图上下间距
        axs[0].set_title("'%s'涨停跌停"%sel)
        if mode=='2分钟':
            axs[0].xaxis.set_major_formatter(MyFormatterRT(D,fmt='m'))
        else:
            axs[0].xaxis.set_major_formatter(kline.MyFormatter(D,'d'))        
        X = np.linspace(0,len(D)-1,len(D))
        xticks = []
        if mode=='2分钟':
            for i in range(len(D)):
                if D[i][0].minute==0 or D[i][0].minute==30:
                    xticks.append(i)
        else:
            for i in range(len(D)):
                if D[i][0].weekday()==0:
                    xticks.append(i)
        xticks.append(len(D)-1)
        xticks.append(len(D)-1)
        xticks.append(len(D)+pos)
        xticks.append(len(D)+pos)            
        if sel=='全部':
            r = K[:,:,2]/K[:,:,3]-1
            um = np.count_nonzero(r>=0.097,axis=0)
            dm = np.count_nonzero(r<=-0.097,axis=0)            
            axs[0].plot(X,um,color="red",label="涨停%d"%(um[-1]))
            axs[0].plot(X,dm,color="green",label="跌停%d"%(dm[-1]))            
        elif sel=='涨停热点' or sel=='跌停热点':
            hots = uhots if sel=='涨停热点' else dhots
            for category in hots:
                sr = idd[:,3]==category
                r = K[sr,:,2]/K[sr,:,3]-1
                if sel=='涨停热点':
                    m = np.count_nonzero(r>=0.097,axis=0)
                else:
                    m = np.count_nonzero(r<=-0.097,axis=0)
                if hot==category:
                    axs[0].plot(X,m,linewidth=3,label=category)
                else:
                    axs[0].plot(X,m,linestyle='--',alpha=0.5,label=category)
        else:
            #选择分类的涨停和跌停
            sr = idd[:,3]==sel
            r = K[sr,:,2]/K[sr,:,3]-1
            um = np.count_nonzero(r>=0.097,axis=0)
            dm = np.count_nonzero(r<=-0.097,axis=0)            
            axs[0].plot(X,um,color="red",label="涨停%d"%(um[-1]))
            axs[0].plot(X,dm,color="green",label="跌停%d"%(dm[-1]))

        axs[0].axvline(len(D)+pos,color="red",linewidth=2,linestyle='--')
        axs[0].set_xticks(xticks)
        axs[0].legend()
        axs[0].grid(True)
        axs[0].set_xlim(0,len(D))  
        plt.setp(axs[0].get_xticklabels(),rotation=20,horizontalalignment='right')

        dr = K[:,pos,2]/K[:,pos,3]-1
        def autolabel(rects):
            """Attach a text label above each bar in *rects*, displaying its height."""
            for rect in rects:
                height = rect.get_height()
                axs[1].annotate('{}'.format(height),
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')  
        def getcols(s,c):
            a = []
            for v in s:
                a.append(v[c])
            return a
        S = []
        if sel=='全部':
            for category in allCategory():
                sr = idd[:,3]==category
                upset = dr[sr]>=0.097
                downset = dr[sr]<=-0.097
                uns = np.count_nonzero(upset)
                dns = np.count_nonzero(downset)
                if uns>0 or dns>0:
                    coms = []
                    for cidd in K[sr,pos,0][upset]:
                        coms.append(id2com[int(cidd)])
                    for cidd in K[sr,pos,0][downset]:
                        coms.append(id2com[int(cidd)])                        
                    S.append((category,uns,dns,coms))
            SS = sorted(S,key=lambda it:100*it[1]-it[2],reverse=True)
            labels = getcols(SS,0)
            ums = getcols(SS,1)
            dms = getcols(SS,2)
            x = np.arange(len(labels))  # the label locations
            width = 0.4  # the width of the bars
            if method=='None':                
                rects1 = axs[1].bar(x - width/2, ums, width, color='red', label='涨停')
                rects2 = axs[1].bar(x + width/2, dms, width, color='green',label='跌停') 
                autolabel(rects1)
                autolabel(rects2)
            else:
                #计算昨天涨停的次日的平均涨落
                t = datetime.today()
                ei = len(D)+1
                Nam = np.zeros(len(D))
                for i in range(len(D)-1,-1,-1): #反向搜索
                    if D[i][0].day!=t.day:
                        t = D[i][0]
                        r = K[:,i,2]/K[:,i,3]-1
                        s = r>=0.097
                        if ei>i+1 and np.count_nonzero(s)>0:
                            Nam[i+1:ei] = np.mean((K[s,i+1:ei,2]/K[s,i+1:ei,3]-1),axis=0)
                        ei = i+1                
                axs[1].plot(X,Nam,color="red",label="次日平均涨幅")
            clear_output2()
            if listState:
                if SS is not None:
                    list_output2_category(SS)                
        else:
            if sel=='涨停热点' or sel=='跌停热点':
                sr = idd[:,3]==hot
            else:
                sr = idd[:,3]==sel
            idds = idd[sr]
            R = dr[sr]*100
            for i in range(len(R)):
                rate = R[i]
                S.append((idds[i,2],rate if rate>0 else 0,rate if rate<0 else 0,idds[i,1]))
            SS = sorted(S,key=lambda it:it[1]+it[2],reverse=True)
            labels = getcols(SS,0)
            ums = getcols(SS,1)
            dms = getcols(SS,2)
            codes = getcols(SS,3)
            x = np.arange(len(labels))  # the label locations
            width = 0.2  # the width of the bars
            if method=='None': 
                rects1 = axs[1].bar(x, ums, 0.9, color='red', label='涨跌分布')
                rects2 = axs[1].bar(x, dms, 0.9, color='green')
                axs[1].axhline(0,color='black',linewidth=2,linestyle='--')
            else:
                t = datetime.today()
                ei = len(D)+1
                Nam = np.zeros(len(D))
                for i in range(len(D)-1,-1,-1): #反向搜索
                    if D[i][0].day!=t.day:
                        t = D[i][0]
                        r = K[sr,i,2]/K[sr,i,3]-1
                        s = r>=0.097
                        if ei>i+1 and np.count_nonzero(s)>0:
                            r = K[sr,i+1:ei,2]/K[sr,i+1:ei,3]-1
                            Nam[i+1:ei] = np.mean(r[s,:],axis=0)
                        ei = i+1                
                axs[1].plot(X,Nam,color="red",label="次日平均涨幅")
            clear_output2()
            if listState:
                list_output2(labels,codes,ums,dms)            
            #autolabel(rects1)
        axs[1].grid(True)
        if method=='None':    
            axs[1].set_xticks(x)
            axs[1].set_xticklabels(labels)
            if len(labels)>90:
                rotate = 90
            elif len(labels)>70:
                rotate = 45
            elif len(labels)>40:
                rotate = 30
            else:
                rotate = 20
            plt.setp(axs[1].get_xticklabels(),rotation=rotate,horizontalalignment='right')
            axs[1].set_xlim(-1,len(labels))
        kline.output_show(output)
    def update():
        nonlocal first,output,D,K,refreshbutton
        t = datetime.today()
        if first or stock.isTransTime(t):
            refreshbutton.button_style = 'success'
            getData()
            with output:
                update_zdt()
            refreshbutton.button_style = ''
        if t.hour>=6 and t.hour<15:
            xueqiu.Timer(120,update)
        first = False
    update()        

"""
指数分类界面
"""
def K(code,pos=None):
    if pos is None:
        kline.Plote(code,'d',config={'index':True},mode='runtime').show()
    else:
        kline.Plote(code,'d',config={'index':True},mode='auto',lastday=10*365).show(pos=pos)

def Indexs():
    menus = {
        "大盘":['SH000001', #上证
            'SZ399001', #深成
            'SZ399006'],#创业
        "科技":['BK0021', #半导体
            'BK0489', #5G
            'BK0444', #大数据
            'BK0063', #计算机应用
            'BK0414',#云计算 *
            'BK0626',#消费电子 *
            'BK0586',#芯片概念 *
            'BK0441',#新能源汽车 *
            'BK0022', #光学光电子
            'BK0029', #通信设备
            'BK0066', #国防军工
            'BK0410'], #稀土永磁
        "金融":["BK0057", #证券
            "BK0055", #银行
            "BK0056"], #保险
        "消费":[
            'BK0033', #饮料
            'BK0034', #食品加工
            'BK0638', #农业种植
            'BK0040', #化学制药
            'BK0044', #医疗器械
            'BK0031' #家电
        ],
        "基建":[
            'BK0018', #专用设备
            'BK0436', #特高压
            'BK0608', #水泥
            'BK0015', #建筑材料
            'BK0013' #有色冶炼加工
        ]
    }
    buts = []
    oldbut = None
    def onClick(e):
        nonlocal menus,oldbut
        if oldbut is not None:
            oldbut.button_style = ''
        e.button_style = 'warning'
        output.clear_output()
        with output:
            for code in menus[e.description]:
                K(code)
        oldbut = e
        e.button_style = 'success'
    for m in menus:
        but = widgets.Button(description=m)
        buts.append(but)
        but.on_click(onClick)
    output = widgets.Output()
    box_layout = Layout(display='flex',
                    flex_flow='wrap',
                    align_items='stretch',
                    border='solid',
                    width='100%')    
    
    box = Box(children=buts,layout=box_layout)
    display(box,output)
    onClick(buts[0])

"""
显示大盘涨跌周期个股和分类的涨跌情况
"""
def fluctuation():
    output = widgets.Output()
    display(output)
    companys = stock.query("""select company_id,code,name,category from company_select""")
    step = 1
    szi = 0
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
    for i in range(len(companys)):
        if companys[i][1]=='SH000001':
            szi = i
            break
    def plote_fluctuation(result,output):
        fig,axs = plt.subplots(2,1,figsize=(30,14))
        fig.subplots_adjust(hspace=0.1,wspace=0.05) #调整子图上下间距
        axs[0].set_title("涨跌分布")

        kline.output_show(output)
    def update_fluctuation(K,D):
        eps = stock.extremePoint(K[szi,:,3])
        i0,i1,i2 = 0,0,0
        dK1 = K[:,i1,3]/K[:,i0,3]-1
        dK2 = K[:,i2,3]/K[:,i1,3]-1
        result = []
        for category in allCategory():
            r = idd[:,3]==category
            r1 = dK1[r].mean()
            r2 = dK2[r].mean()
            result.append((category,r1,r2))
        with output:
            plote_fluctuation(result,output)
    def update():
        nonlocal companys,step
        t = datetime.today()
        if stock.isTransTime(t):
            K,D = xueqiu.getRT(companys,step=step)
            update_fluctuation(K,D)
        if t.hour>=6 and t.hour<15:
            xueqiu.Timer(120,update)
    update()