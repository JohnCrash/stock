from ipywidgets.widgets.widget_selection import Dropdown
from IPython.display import display,Markdown
import ipywidgets as widgets
from ipywidgets import Layout, Button, Box
from datetime import date,datetime,timedelta
import numpy as np
from requests.models import codes
from . import shared
from . import stock
from . import xueqiu
from . import kline

ETFs = [ 
    'SZ159919', #沪深300ETF
    'SH510050', #上证50ETF
    'SZ159949', #创业板50
    'SH588000', #科创板50ETF
    'SZ159995', #芯片
    'SZ159997', #电子ETF
    'SH515980', #人工智能
    'SH512720', #计算机
    'SZ159994', #5GETF
    'SH512660', #军工
    'SH515700', #新能源车ETF
    'SH512580', #环保
    'SH515790', #光伏
    'SH512800', #银行
    'SH512000', #券商
    'SZ159992', #创新药
    'SH512010', #医药ETF
    'SH512170', #医疗ETF
    "SZ159825", #农业ETF
    'SH512690', #酒
    'SH510150', #消费ETF
    'SZ159996', #家电
    'SH512980', #传媒ETF
    'SH512400', #有色金属ETF
    'SH512580', #环保
    'SH512200', #房地产
    "SH515210", #钢铁
    "SH515220"  #煤炭
]
BCs = [
    "SH601318",#平安
    "SH601985",#中国核电
    "SH603986", #兆易创新
    "SZ002371", #北方华创
    "SH600584", #长电科技
    "SH603160",#汇顶科技
    "SH688981", #中芯国际-U
    "SZ000725", #京东方A
    "SZ002475", #立讯精密
    "SZ002241",#歌儿股份
    "SH603501",#韦尔股份
    "SZ000063", #中兴通信
    "SZ002230", #科大讯飞
    "SZ002415", #海康威视
    "SZ002049", #紫光国微
    "SH601633", #长城汽车
    "SZ002594", #比亚迪
    "SZ000625", #长安汽车
    "SH600104", #上汽集团
    "SZ300750",  #宁德时代
    "SH600030", #中信证券
    "SH600031",#三一重工
    "SZ000425",#徐工
    "SH601088",#中国神华
    "SH600585", #海螺水泥
    "SH600720",#祁连山
    "SZ000333",#美的
    "SZ000651",#格力
    "SZ000858",#五粮液
    "SH600809", #山西汾酒
    "SZ000568",#泸州老窖
    "SH600276",#恒瑞医药
    "SH600196",#复兴医药
    "SZ300122",#智飞生物
    "SZ300015",#爱尔眼科
    "SH601899",#紫金矿业
    "SZ000878",#云南铜业
    "SH600887"#伊利股份
]
"""
指数分类界面
"""
def K(code,period=None,pos=None):
    if pos is None:
        kline.Plote(code,period,config={'index':True},mode='runtime').show()
    else:
        kline.Plote(code,period,config={'index':True},mode='auto',lastday=10*365).show(pos=pos)

def indexpage(menus):
    buts = []
    oldbut = None
    def onClick(e):
        nonlocal menus,oldbut,output
        if oldbut is not None:
            oldbut.button_style = ''
        e.button_style = 'warning'
        xueqiu.clearTimer() #清楚标签下的全部更新
        output.clear_output()
        with output:
            for code in menus[e.description]:
                if type(code)==str:
                    K(code)
                elif callable(code):
                    code()
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
    #onClick(buts[0])
    def cb():
        onClick(buts[0])
    xueqiu.setTimeout(.1,cb,'indexpage')

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
                    kline.Plote(i[2].upper(),config={'index':True,'markpos':i[1]},prefix="%s %s "%(i[4],i[5]),context='关注',mode='runtime').show()
                    
        but.on_click(on_click)
        items.append(but)
    box = Box(children=items,layout=Layout(display='flex',
            flex_flow='wrap',
            align_items='stretch',
            border='solid',
            width='100%'))    
    display(box,out)

"""
返回在5日均线上穿10日均线的概念和分类
"""
def getMaRise(prefix='90',period=240,mas=[5,10,20,30,60]):
    K,D = xueqiu.get_period_k(period)
    mav = []
    for i in mas:
        mav.append(stock.maMatrix(K,i))
    companys = xueqiu.get_company_select()
    R = []
    def isRise(i):
        for k in range(1,len(mav)):
            if mav[k-1][i,-1] < mav[k][i,-1]:
                return False
        return True
    for i in range(len(companys)):
        c = companys[i]
        if c[1][0]=='B' and c[3]==prefix and isRise(i):
            R.append(c[1])
    return R

"""
返回最近nday天排名前top的概念或者分类
[
    [0.分类代码],
    [1.概念代码]
]
"""
def getDTop(perfix='90',top=3,nday=20,K=None):
    companys = xueqiu.get_company_select()
    if K is None:
        K,D = xueqiu.get_period_k(240)    
    dk = (K[:,1:]-K[:,0:-1])/K[:,0:-1]

    result = {}
    for i in range(-1,-nday-1,-1):
        s = []
        for j in range(K.shape[0]):
            if companys[j][3]==perfix:
                s.append((j,dk[j,i]))
        s = sorted(s,key=lambda it:it[1],reverse=True)
        for j in range(top):
            comi = s[j][0]
            if comi in result:
                result[comi] = result[comi]+1
            else:
                result[comi] = 1
            comlow = s[-j-1][0]
            if comlow in result:
                result[comlow] = result[comlow]-1
            else:
                result[comlow] = -1
    R = []
    r = sorted(result.items(),key=lambda it:it[1],reverse=True)
    for it in r:
        i = it[0]
        n = it[1]
        #print(companys[i],n)
        if n>0:
            R.append(companys[i][1])

    return R

"""
返回当前涨幅排名前3
"""
def getTodayTop(perfix='90',top=3,K=None):
    companys = xueqiu.get_company_select()
    if K is None:
        K,D = xueqiu.get_period_k(240)
    dk = (K[:,-1]-K[:,-2])/K[:,-2]
    s = []
    for j in range(K.shape[0]):
        if companys[j][3]==perfix:
            s.append((j,dk[j]))
    s = sorted(s,key=lambda it:it[1],reverse=True)
    R = []
    for i in range(top):
        R.append(companys[s[i][0]][1])
    return R

def Indexs():
    global ETFs,BCs
    menus = {
        "大盘":['SH000001', #上证
            'SZ399001', #深成
            'SZ399006'],#创业
        "上榜分类":getDTop('90',3),
        "上榜概念":getDTop('91',15),
        "ETF":ETFs,
        "自选":BCs,
        "关注":[favoriteList]
    }
    indexpage(menus)

def Monitor():
    menus = {
        "机会":[moniter]
    }
    indexpage(menus)

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
    return False,(0,0,0)
"""
从尾部向前搜索中枢
方法:先确定一个高点范围，和低点范围，然后如果k在高点和低点之间交替超过2次
返回b,(通道长度，上限，下限)
"""
def bollway(k,n=16,jcn=3):
    if len(k)>n:
        argv = k[-n-1:-1].mean()
        maxv = np.amax(k[-n-1:-1])
        minv = np.amin(k[-n-1:-1])
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
            return zfn>jcn,(N,minv,maxv) #最少要交替3次
    return False,(0,0,0)
"""
boll通道由平直到打开返回True,否则返回False
通道检查n个点，通道宽度都要小于p
"""
def bollopenk(k,period=240,n=16):
    if len(k)>n and k[-1]>k[-2] and k[-1]>k[-3] and k[-1]>k[-4]: #快速过滤掉大部分的
        b,(N,minv,maxv)=bollwayex(k[:-1],n)
        return b and k[-1]>maxv
    return False

"""
三角形整理
最高偏离至少要大于p,最少要回归到最大值的q的位置,大于均线的k线个数要大于n
返回b, (起涨点bi,最大点maxi)
"""
def trianglek(k,ma,p=0.02,q=1/2,n=5):
    dk = k-ma
    maxdk = 0
    maxi = 0
    if dk[-1]>0:
        for i in range(-1,-len(dk)-1,-1):
            if dk[i]>0:
                if dk[i] > maxdk:
                    maxdk = dk[i]
                    maxi = i
            else:
                #要求最大要大于一个阈值
                if maxi!=0 and maxi-i>=n:
                    maxr = maxdk/ma[maxi] #最大点高于均线的比率
                    endr = dk[-1]/ma[-1] #最后点高于均线的比率
                    if maxr>p and  endr/maxr < q:
                        return True,(i,maxi)
                return False,(i,maxi)
    return False,(0,0)
"""
股价先大幅高于均线ma,然后开始回落到ma返回True,否则返回False
最高偏离至少要大于p,最少要回归到最大值的q的位置,大于均线的k线个数要大于n
"""
def maclose(k,ma,p=0.02,q=1/3,n=5):
    b,_ = trianglek(k,ma,p,q,n)
    return b

"""
对当前的事件进行组合提取
返回一个
{
    code:[(type,period,time)]
}
"""
def combo_event(E):
    companys = xueqiu.get_company_select()
    code2c = {}
    for c in companys:
        code2c[c[1]] = c
    event = E['event'][-1]
    R = {}
    t = E['seqs'][-1]
    def comboc(s,c):
        LS = []
        for m in ['fl_top','gn_top','bollopen','maclose']:
            if m in E and c in E[m]:
                for p in E[m][c].items():
                    LS.append((m,p[0],p[1]))
        if len(LS)>0: #必须有一个其他的事件
            LS.append((s,0,t))
            R[c] = LS
    for s in ['fl_topup','gn_topup','fastup','highup']:
        if s in event:
            for c in event[s]:
                comboc(s,c)
    return R
"""
监视在均线附近
1.boll通道向上(15分钟,30分钟,60分钟,日线)
2.触碰重要均线向上(5日,10日,20日,60日)
3.涨幅排名(首次进入排名，n次进入排名)
4.快速上涨
E = {
    "fl_top":{ #分类排行
        code:{
            period:add_time
        },
        ...
    },
    "gn_top":{ #概念排行
        code:{
            period:add_time
        },
        ...
    },
    "bollopen":{
        code:{
            period:add_time
        },
        ...
    },
    "maclose":{
        code:{
            period:add_time
        },
        ...
    },
    "fl_top3":[] #当日分类排行
    "gn_top3":[] #当日概念排行
    "seqs":[
        每次进行执行moniter_loop的时间列表
    ],
    "event":[
        {"fl_topup":[],"gn_topup":[],"fastup":[],"highup":[]},
        ....
    ]
}
E 和 offset用于模拟
"""
def moniter_loop(E=None,offset=None,periods=[15,30,60,240]):
    t = datetime.today()
    companys = xueqiu.get_company_select()
    K = {}
    D = {}    
    for period in periods:
        K[period],D[period] = xueqiu.get_period_k(period)
    ename = 'event%d%d'%(t.month,t.day)
    if E is None:
        b,E = shared.fromRedis(ename)
    else:
        b = True
    def add(es,com,period,arg=None):
        nonlocal t
        if es not in E:
            E[es] = {}
        if com not in E[es]:
            E[es][com] = {}
        if period not in E[es][com]:
            E[es][com][period] = t
    if not b:
        E = {}
        tops = getDTop('90',3,K=K[240]) #初始化日排行榜
        for c in tops:
            add('fl_top',c,240)
        tops = getDTop('91',15,K=K[240]) #初始化日排行榜
        for c in tops:
            add('gn_top',c,240)
        E['seqs'] = [t]
        E['event'] = []
        E['fl_top3'] = []
        E['gn_top3'] = []
    else:
        E['seqs'].append(t)
    #1.boll通道向上(15分钟,30分钟,60分钟,日线)
    for period in periods:
        k = K[period]
        ma20 = stock.maMatrix(k,20)
        for i in range(len(companys)):
            if k[i,-1]>ma20[i,-1] and bollopenk(k[i,:],period): #对于在20均线上的才做检查
                add('bollopen',companys[i],period)
    #2.触碰重要均线向上(5日,10日,20日,60日)
    cma = [
        [30,40,5],#使用period=30的40均线,就是5日线做检查
        [30,80,10],
        [240,20,20],
        [240,60,60]
    ]
    for p in cma:
        k = K[p[0]]
        ma = stock.maMatrix(k,p[1])
        for i in range(len(companys)):
            if k[i,-1]>=ma[i,-1] and maclose(k[i,:],ma[i,:]):
                add('maclose',companys[i],p[2])
    #3.涨幅排名(首次进入排名，n次进入排名)
    event = {}
    for it in [('90',3,'fl_top3','fl_topup'),('91',15,'gn_top3','gn_topup')]:
        new_top3 = getTodayTop(it[0],it[1],K[240])
        old_top3 = E[it[2]]
        news = []
        for c in new_top3:
            if c not in old_top3:#新上榜
                news.append(c)
        if len(news)>0:
            event[it[3]] = news
        E[it[2]] = new_top3
    b,r,d = xueqiu.getTodayRT()
    if offset is not None:
        r = r[:,:offset,:]
    if b:
    #4.快速上涨(使用分时图进行检查)
        if r.shape[1]==1:
            highup = []
            for i in range(r.shape[0]):
                if r[i,-1,1]>=0.5: #高开大于0.5%的
                    highup.append(companys[i][1])
            if len(highup)>0:
                event['highup'] = highup
        else:
            fastup = []
            for i in range(r.shape[0]):
                if r[i,-1,1]-r[i,-2,1]>=0.5: #1分钟涨幅大于0.5%的
                    fastup.append(companys[i][1])
            if len(fastup)>0:
                event['fastup'] = fastup
    #5.平静到快速上涨
    E['event'].append(event) #将E保存
    #shared.toRedis(E,ename,ex=7*24*3600)
    return combo_event(E),E
"""
"""
def monitor():
    pass