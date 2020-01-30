"""
对所有股票进行计算
计算器日macd，周macd，日能量，周能量，日成交量kdJ,周成交量kdJ
算法是增量优化的，每次运行仅仅计算增加的部分
"""
import numpy as np
import stock
import xueqiu
import kline
from datetime import date
from IPython.display import display
import ipywidgets as widgets
from ipywidgets import Layout, Button, Box
from datetime import date,datetime,timedelta
import matplotlib.pyplot as plt
import math
import shared

PROD = 40

def isPopularCategory(name): #如果是主流分类返回True
    ls = ['半导体','光学光电子','计算机应用','电子制造','生物制品','通信设备','医药商业','饮料制造','多元金融','生物制品',
          '证券','互联网传媒','化学制药','医疗器械','文化传媒','元件','高低压设备','环保工程及服务','地面兵装','专业工程',
          '其他电子','营销传播','视听器材','电气自动化设备','医疗服务','专用设备','计算机设备','电源设备','贸易','专用设备']
    return name in ls

#见数据插入到company_status表
def insert_company_status(k,vma20,energy,volumeJ,idd):
    if len(k)>0:
        qs = ""
        for i in range(len(k)):
            #id , date , close , volume , volumema20 , macd , energy , voluemJ
            try:
                macd = 0 if k[i][3] is None else k[i][3]
                if i!=len(k)-1:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f),"""%(k[i][0],stock.dateString(idd[i]),k[i][2],k[i][1],vma20[i],macd,energy[i],volumeJ[i])
                else:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f)"""%(k[i][0],stock.dateString(idd[i]),k[i][2],k[i][1],vma20[i],macd,energy[i],volumeJ[i])
            except Exception as e:
                print(e)
                print(k[i])
                print(idd[i])
        stock.execute("insert ignore into company_status values %s"%(qs))

#bi是更新点-1插入全部
def update_company_status_week(cid,k,macd,vma20,energy,volumeJ,idd,bi):
    if len(k)>0:
        #下面更新接头部分的值
        i = bi
        if bi>0:
            qs = "update company_status_week set close=%f,volume=%f,macd=%f,volumema20=%f,energy=%f,volumeJ=%f where id=%d and date='%s'"%(k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i],cid,stock.dateString(idd[i][0]))
            stock.execute(qs)

        #下面是插入新的值
        if bi+1<len(k):
            qs = ""
            for i in range(bi+1,len(k)):
                #id , date , close , volume , macd , volumema20 , energy , voluemJ
                #k0 volume,1 open,2 high,3 low,4 close
                if i!=len(k)-1:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f),"""%(cid,stock.dateString(idd[i][0]),k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i])
                else:
                    qs+="""(%d,'%s',%f,%f,%f,%f,%f,%f)"""%(cid,stock.dateString(idd[i][0]),k[i][4],k[i][0],macd[i],vma20[i],energy[i],volumeJ[i])
            stock.execute("insert ignore into company_status_week values %s"%(qs))

#依据完整数据更新
def update_company_status_all_data(idk,idd):
    k = np.array(idk)
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]

    insert_company_status(k,vma20,energy,volumeJ,idd)

#依据增量数据更新
def update_company_status_delta_data(idk,idd):
    k = np.array(idk)
    vma20 = stock.ma(k[:,1],20)
    energy = stock.kdj(stock.volumeEnergy(k[:,1]))[:,2]
    volumeJ = stock.kdj(k[:,1])[:,2]

    insert_company_status(k[PROD+1:],vma20[PROD+1:],energy[PROD+1:],volumeJ[PROD+1:],idd[PROD+1:])

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
            shared.delKey('company_status') #清除redis中的缓存数据
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
    if lastupdate[0][0] == lastday[0][0]:
        progress(100)
        return #已经更新了
    
    shared.delKey('company_status_week') #清除redis中的缓存数据
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
        #计算周macd,volumema20,energy,volumeJ
        WK = np.array(wk)
        macd = stock.macdV(WK[:,4])
        volumema20 = stock.ma(WK[:,0],20)
        energy = stock.kdj(stock.volumeEnergy(WK[:,0]))[:,2]
        volumeJ = stock.kdj(WK[:,0])[:,2]
        #将周数据更新到company_status_week表中
        #相等部分更新，后面部分插入
        update_company_status_week(key,WK,macd,volumema20,energy,volumeJ,wd,bi)
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
        return True
    return False

#最近50天的status数据
#同时返回50天的日期数组和数据
def redisStatusCache50(db):
    b1,a = shared.numpyFromRedis("%s_last50"%(db))
    b2,d = shared.fromRedis("%s_date50"%(db))
    if not (b1 and b2):
        #缓存中没有准备数据
        d = stock.query("""select date from %s where id=8828 order by date desc limit 50"""%(db))
        cs=stock.query("""select id,close,volume,volumema20,macd,energy,volumeJ from %s where date>='%s' and date<='%s'"""%(db,stock.dateString(d[-1][0]),stock.dateString(d[0][0])))
        r = stock.query("""select count(*) from company""")
        n = r[0][0] #公司数量
        a = np.zeros((n,len(d),7))
        lastid = -1
        i = len(d)-1
        nc = -1
        for c in cs:
            if c[0]!=lastid:
                i = len(d)-1
                nc += 1
                lastid = c[0]
                if nc>=n:
                    break
            a[nc,i,:] = c
            i-=1
        shared.numpyToRedis(a,"%s_last50"%(db))
        shared.toRedis(d,"%s_date50"%(db))
    #数据d存放的是时间，d[0]最近的时间 d[-1]最远的时间
    #数据a的时间序列和d相同,shape = (公司数,日期,数据)
    return d,a
    
#这是使用Redis进行优化的版本    
def searchRasingCompanyStatusByRedis(dd,period,cb,id2companys,progress):
    if period=='d':
        db = 'company_status'
    else:
        db = 'company_status_week'
    progress(10)
    d,a = redisStatusCache50(db)
    progress(30)
    istoday = False
    bi = 0
    for i in range(len(d)):
        if str(d[i][0])==dd:
            bi = i
    if bi==0:
        #数据还没有进入数据库
        istoday = xueqiu.isTransTime()

    rasing = []
    n20 = math.floor(len(a)/20)
    for i in range(len(a)):
        c = a[i]
        idd = int(c[-1][0])
        if idd in id2companys and cb(c[bi:,:],id2companys[idd],istoday):
            rasing.append(idd)
        #progress
        if i%n20== 0:
            progress(30+math.floor(70*i/len(a)))
    progress(100)
    return rasing

#找到有崛起继续的个股id , dd是搜索指定日期
def searchRasingCompanyStatus(dd,period,cb,id2companys,progress):
    if period=='d':
        db = 'company_status'
    else:
        db = 'company_status_week'
    lastday = stock.query("""select date from %s where id=8828 order by date desc limit 50"""%(db))
    progress(10)
    endDate = None
    beginDate = None
    istoday = False
    for i in range(len(lastday)):
        if str(lastday[i][0])==dd:
            endDate = lastday[i][0]
            beginDate = lastday[i+2][0]
    if beginDate is None:
        #数据还没有进入数据库
        endDate = lastday[0][0]
        beginDate = lastday[40][0]
        istoday = xueqiu.isTransTime()
    #技能根据id将加载分成9份
#使用分布加载将大幅度增加耗时    
#    css = []
#    t0 = datetime.today()
#    for i in range(1,9):
#        progress(i*10)
#        css+=stock.query("""select id,close,volume,volumema20,macd,energy,volumeJ from %s where date>='%s' and date<='%s' and id>=%d and id<%d"""%(db,stock.dateString(beginDate),stock.dateString(endDate),1000*(i-1),1000*i))
#    print(datetime.today()-t0)
    print(beginDate,endDate)
    css=stock.query("""select id,close,volume,volumema20,macd,energy,volumeJ from %s where date>='%s' and date<='%s'"""%(db,stock.dateString(beginDate),stock.dateString(endDate)))
    cs = np.array(css)
    progress(90)
    stock.closedb()
    idds = {}
    for i in range(len(cs)):
        if cs[i][0] not in idds:
            idds[cs[i][0]] = []
        idds[cs[i][0]].append(cs[i])
    progress(95)
    rasing = []
    for c in idds:
        if len(idds[c])>=3 and c in id2companys and cb(idds[c],id2companys[c],istoday):
            rasing.append(int(c))
    progress(100)
    return rasing

"""
按分类列出崛起的股票的数量与列表
"""
def RasingCategoryList(period='d',cb=isRasing):
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
    id2companys = {}
    for c in companys:
        id2companys[c[0]] = c

    def onCatsList(E):
        nonlocal progress
        progress = widgets.IntProgress(value=0,
            min=0,max=100,step=1,
            description='Loading:',
            bar_style='',
            orientation='horizontal',layout=progress_layout)
        with output2:
            display(progress)            
        progressCallback(0)
        rasing = searchRasingCompanyStatusByRedis(E.description,period,cb,id2companys,progressCallback)
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
        def onClick(e):
            output.clear_output(wait=True)
            key = e.tooltip
            with output:
                display(box)
                for c in cats[key]['ls']:
                    kline.Plote(c[1],period,config={"index":True,"markpos":date.fromisoformat(E.description)}).show(figsize=(32,15))
                
        for c in cats:
            if cats[c]["count"]>0:
                s = "%s %d"%(cats[c]["name"],cats[c]["count"])
                but = widgets.Button(
                    description=s,
                    disabled=False,
                    button_style='',
                    tooltip=c)
                but.on_click(onClick)
                items.append(but)
        box = Box(children=items, layout=box_layout)
        output.clear_output(wait=True)
        with output:
            display(box)

    items = []

    dates = stock.query('select date from %s where id=8828 order by date desc limit 10'%('company_status' if period=='d' else 'company_status_week'))
    today = date.today()
    if period=='d' and dates[0][0] != today:
        #如果今天是一个交易日，并且不在数据库中，那么从雪球直接下载数据
        but = widgets.Button(
            description=str(today),
            disabled=False,
            button_style='danger')
        but.on_click(onCatsList)
        items.append(but)

    for d in dates:
        but = widgets.Button(
            description=str(d[0]),
            disabled=False,
            button_style='')
        but.on_click(onCatsList)
        items.append(but)

    box = Box(children=items, layout=box_layout)
    display(box,output)