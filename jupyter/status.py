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
        update_status_begin('2010-1-2',True,progress)
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

#多线程下载加快速度
def downloadXueqiuK15(tasks,progress,tatoal,ThreadCount=10):
    results = []
    lock = threading.Lock()
    count = 0
    #t[0] = [(0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw),...]
    #t[1] = (0 company_id,1 code,2 name,3 category,4 ttm,5 pb)
    def xueqiuK15(t):
        nonlocal count
        b,k_,d_ = xueqiu.xueqiuKday(t[1][1],15)
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

"""
前置过滤器，用于初选。这样在处理当日数据下载时可以少下载很多数据
"""
def defaultFilter(a,c,istoday,period):
    #istoday True可以使用xueqiu数据
    #c [0 company_id,1 code,2 name,3 category,4 ttm,5 pb]
    #a 0 id , 1 close , 2 volume , 3 volumema20 , 4 macd , 5 energy ,6 volumeJ ,7 bollup ,8 bollmid,9 bolldn,10 bollw
    #a[0] a[1] a[2]... a[0]是最近一天的数据
    if istoday and period=='d':
        return isPopularCategory(c[3])
    else:
        return isPopularCategory(c[3])

"""
按分类列出崛起的股票的数量与列表
"""
def RasingCategoryList(period='d',cb=isRasing,filter=defaultFilter,name=None):
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
        rasing,vlines = searchRasingCompanyStatusByRedis(E.date,period,cb,filter,id2companys,progressCallback)
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
                    for vline in vls:
                        if 'x' in vline:
                            vline['dates'] = []
                            for i in vline['x']:
                                vline['dates'].append(index2date(i)) #将负索引转换为日期
                    #kline.Plote(c[1],period,config={"index":True,"markpos":current_date,"vlines":vls}).show(figsize=(32,15))
                    kline.Plote(c[1],period,config={"index":True,"vlines":vls}).show(figsize=(32,15))
        
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
    
    for i in range(15):
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
            #self.reload(all=False)
            #showline()
            xueqiu.Timer(xueqiu.nextdt15()+1,updatek15)
    if today_but is not None:
        xueqiu.Timer(xueqiu.nextdt15()+1,updatek15)

#最近N天的status数据
#同时返回N天的日期数组和数据
def getStatusN(db,N):
    #缓存中没有准备数据
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
[
    (0 周期,1 分类名称,2 周期盈利二维数组np.array[company_n,date_n],3 日期列表[(date,),...],
     4 np.array[(0 id , 1 code , 2 name , 3 category),],5 按周期利润排序的索引和利润对[company,date,(index,dk)],
     6 该分类的前十名平均盈利[date],
    ...
]
"""
def StrongSorted(days,N=50):
    result = []
    #categorys = stock.query("""select id,name from category""")
    companys = stock.query("""select company_id,code,name,category from company_select""")
    id2com = {}
    for com in companys:
        id2com[com[0]] = com
    if N>50:
        D,K = getStatusN('company_status',N)
    else:
        D,K = redisStatusCache50('company_status')
    idd = np.empty((len(K),4),dtype=np.dtype('O')) #(0 id , 1 code , 2 name , 3 category)
    idd[:,0] = K[:,0,0]
    for i in idd:
        k = int(i[0])
        if k in id2com:
            i[1] = id2com[k][1]
            i[2] = id2com[k][2]
            i[3] = id2com[k][3]
    
    for day in days:
        dk = (K[:,day:,1]-K[:,:-day,1])/K[:,:-day,1]
        for category in popularCategory():
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
                for i in range(dK.shape[1]):
                    top10mean[i] = sorti[:10,i,1].mean()
                result.append((day,category,dK,D[day:],idd[r],sorti,top10mean))
            else:
                print("'%s' 分类里面没有公司"%category)
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

def PlotCategory(bi,ei,pos,r,top=None,focus=None):
    fig,axs = plt.subplots(figsize=(28,14))
    dd = r[3] #date
    axs.xaxis.set_major_formatter(kline.MyFormatter(dd,'d'))
    if top is None:
        axs.set_title("%s 周期%s"%(r[1],r[0]))
    else:
        axs.set_title("%s 周期%s Top%s"%(r[1],r[0],top))
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
    plt.show()

"""
按分类列出强势股
"""
def StrongCategoryCompanyList(category,name):
    def getResult(day,categoryName):
        nonlocal category
        for r in category:
            if r[0]==day and r[1]==categoryName:
                return r
        return None

    period = 20
    top = 10
    com = None
    result = getResult(period,name)
    pagecount = 50
    LEN = len(result[3])
    bi = LEN-pagecount
    ei = LEN    
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
        options=[3,5,10,20],
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
        nonlocal top,pos,result,name
        output2.clear_output(wait=True)
        with output2:
            for i in range(top):
                if i < len(result[5]):
                    inx = int(result[5][i,pos,0])
                    r = result[4][inx] #(0 id , 1 code , 2 name , 3 category)
                    dd = result[3][pos][0]
                    kline.Plote(r[1],'d',config={'index':True,'markpos':dd},context="强势分类 %s %d"%(name,i+1)).show()

    butList.on_click(onListClick)
    out = widgets.Output()
    box_layout = Layout(display='flex',
                    flex_flow='wrap',
                    align_items='stretch',
                    border='solid',
                    width='100%')    
    stopUpdate = False
    def sortCompanyList():
        nonlocal pos,result,periodDropdown,stopUpdate
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
        nonlocal bi,ei,pos,stopUpdate,needUpdateSlider
        if stopUpdate:
            return
        output.clear_output(wait=True)
        with output:
            PlotCategory(bi,ei,pos,result,top=top,focus=com)
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
        ei = LEN      
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
        nonlocal com,box,stopUpdate,pos,result
        com = e['new']
        if stopUpdate:
            return
        if com is None:
            out.clear_output()
            output2.clear_output()
        else:
            out.clear_output(wait=True)
            with out:
                display(widgets.HTML(value="""<a href="https://xueqiu.com/S/%s" target="_blank" rel="noopener">%s</a>"""%(getCodeByName(com),com)))             
        
        if com is None:                
            showPlot()
        else:
            showPlot()
            output2.clear_output(wait=True)
            with output2:
                dd = result[3][pos][0]
                kline.Plote(getCodeByName(com),'d',config={'index':True,'markpos':dd},context="强势分类 %s"%(name)).show()

    comDropdown.observe(on_com,names='value')

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
        nonlocal bi,ei,pos,pagecount,LEN
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
        if pos>LEN-1:
            pos=LEN-1
        needUpdateSlider = False
        slider.value = pos
        showPlot()
    def on_sliderChange(e):
        nonlocal pos,needUpdateSlider
        pos = e['new']
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


def PlotAllCategory(bi,ei,pos,sortedCategory,top,focus=None):
    fig,axs = plt.subplots(figsize=(28,14))
    r = sortedCategory[0]
    dd = r[3] #date

    axs.xaxis.set_major_formatter(kline.MyFormatter(dd,'d'))
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
    for r in sortedCategory:
        color = getmycolor(r[1])
        dk = r[6] #
        title = "%d %s"%(i+1,r[1])
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
    plt.show()

"""
强势分类于强势股
"""
def StrongCategoryList(N=50):
    def progressCallback(i):
        pass
    update_status(progressCallback) #更新公司日状态
    result = StrongSorted([3,5,10,20],N)
    output = widgets.Output()
    def getSortedCategory(day,pos):
        categorys = []
        for r in result:
            if r[0]==day:
                categorys.append(r)
        if pos > len(categorys[0][6])-1:
            pos = len(categorys[0][6])-1
        if pos < -len(categorys[0][6]):
            pos = -len(categorys[0][6])
        return sorted(categorys,key=lambda it:it[6][pos],reverse=True)

    period = 20
    sortedCategory = getSortedCategory(period,-1)
    top = 10
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
        options=[3,5,10,20],
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
        layout=Layout(display='block',width='196px'),
        disabled=False)        
    categoryDropdown = widgets.Dropdown(
        options=categoryListItem(),
        value=category,
        description='选择分类',
        layout=Layout(display='block',width='196px'),
        disabled=False)

    needUpdateSlider = True
    def showPlot():
        nonlocal output,category,mark,period,top,sortedCategory,result,bi,ei,pos,needUpdateSlider
        if category is None:
            output.clear_output(wait=True)
            with output:
                PlotAllCategory(bi,ei,pos,sortedCategory,top,mark)
        else:
            output.clear_output()
            with output:
                StrongCategoryCompanyList(result,category)
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
    
    def on_top(e):
        nonlocal top
        top = e['new']
        listDropdown.value = None
        showPlot()

    topDropdown.observe(on_top,names='value')
    
    def on_list(e):
        nonlocal top,pos,category,sortedCategory
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
                                kline.Plote(idds[inx,1],'d',config={'index':True,'markpos':dd},context="强势分类 %s %d"%(r[1],j+1)).show()

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
        nonlocal period,pos,needUpdateSlider,category,sortedCategory
        pos = e['new']
        sortedCategory = getSortedCategory(period,pos)       
        if needUpdateSlider and category is None:
            showPlot()

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
        box = Box(children=[backbutton,slider,frontbutton,periodDropdown,topDropdown,listDropdown,markDropdown,categoryDropdown],layout=box_layout)
    else:
        box = Box(children=[prevbutton,nextbutton,zoominbutton,zoomoutbutton,backbutton,slider,frontbutton,periodDropdown,topDropdown,listDropdown,markDropdown,categoryDropdown],layout=box_layout)

    display(box,output)
    showPlot()
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
                    kline.Plote(i[2].upper(),'d',config={'index':True,'markpos':i[1]},prefix="%s %s "%(i[4],i[5]),context='关注',mode='runtime').show()
                    
        but.on_click(on_click)
        items.append(but)
    box = Box(children=items,layout=Layout(display='flex',
            flex_flow='wrap',
            align_items='stretch',
            border='solid',
            width='100%'))    
    display(box,out)