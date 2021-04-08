from ipywidgets.widgets.widget_selection import Dropdown
from IPython.display import display,Markdown
import ipywidgets as widgets
from ipywidgets import Layout, Button, Box
from datetime import date,datetime,timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import math
import numpy as np
from numpy.lib.function_base import disp
from . import shared
from . import stock
from . import xueqiu
from . import kline

box_layout = Layout(display='flex',
                flex_flow='wrap',
                align_items='stretch',
                border='solid',
                width='100%')
class MyFormatterRT(Formatter):
    def __init__(self, dates,fmt='d h:m:s'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0 or math.ceil(x)!=math.floor(x):
            return ''

        t = self.dates[ind]
        if type(t)!=datetime:
            t = t[0]
        if self.fmt=='m-d h:m':
            return '%02d-%02d %02d:%02d'%(t.month,t.day,t.hour,t.minute)
        elif self.fmt=='d h:m:s':
            return '%d %02d:%02d:%02d'%(t.day,t.hour,t.minute,t.second)
        elif self.fmt=='d h:m':
            return '%d %02d:%02d'%(t.day,t.hour,t.minute)
        elif self.fmt=='h:m:s':
            return '%02d:%02d:%02d'%(t.hour,t.minute,t.second)
        elif self.fmt=='h:m':
            return '%02d:%02d'%(t.hour,t.minute)
        else:
            return '%d %02d:%02d'%(t.day,t.hour,t.minute)      

"""
绘制分时图
ax 绘制句柄数组,k (),d 日期,title 标题,style绘制风格
"""
defaultPlotfsStyle = {
    'pcolor':'steelblue',
    'klinewidth':2,
    'ma60color':'darkorange',
    'ma60linewidth':1,
    'ma60linestyle':'dashed',
    'maincolor':'fuchsia',
    'tingcolor':'cornflowerblue'
}
def plotfs(ax,k,d,title,bolls=None,style=defaultPlotfsStyle):
    ax[0].set_title(title,y=0.93)
    x = np.arange(k.shape[0])
    xticks = [0,60-15,2*60-15,3*60+15,4*60+15]
    ax[0].axhline(y=0,color='black',linestyle='dotted')
    ax[0].plot(x,k[:,1],color=style['pcolor'])
    m60 = stock.ma(k[:,1],60)
    ax[0].plot(x,m60,color=style['ma60color'],linestyle=style['ma60linestyle'])#分时均线
    if len(ax)==2:
        ax[1].axhline(y=0,color='black',linestyle='dotted')
        ax[1].plot(x,k[:,3]+k[:,4],color=style['maincolor']) #主力
        ax[1].plot(x,k[:,6],color=style['tingcolor']) #散
        ax[1].set_xlim(0,15+4*60)
        ax[1].set_xticks(xticks)
        ax[1].xaxis.set_major_formatter(MyFormatterRT(d,'h:m'))
        bottom,top = ax[1].get_ylim()
        ax[1].broken_barh([(0,15)], (bottom,top-bottom),facecolor='blue',alpha=0.05)    
    else:
        ax[0].xaxis.set_major_formatter(MyFormatterRT(d,'h:m'))
    ax[0].set_xticks(xticks)
    ax[0].set_xlim(0,15+4*60)
    ax[0].grid(True)
    ax[1].grid(True)
    #ax[0].set_ylim(-10,10)
    """
    bolls = [(0 period,1 price,2 tbi 3 tei,4 up 5 down ,6 isnew今天新的, 7 类型(up,top,mid,bottom,down),8 bo),...]
    bo = (0 timestramp,1 period,2 n,3 up,4 down,5 mink,6 maxk,7 tbi,8 tei,9 zfn)
    绘制和突破点的关系标注
    """
    if bolls is not None:
        openp = k[-1,0]/(1.+k[-1,1]/100.)
        period2c = {5:(3,'forestgreen','dotted'),15:(3,'royalblue','dotted'),30:(3,'fuchsia','dashed'),60:(4,'darkorange','dashdot'),240:(5,'red','dotted')}
        offy = -20
        for boll in bolls:
            if boll[7]=='up':
                y = 100.*(boll[4]-openp)/openp
            elif boll[7]=='down':
                y=100.*(boll[5]-openp)/openp
            else:
                continue
            ax[0].axhline(y=y,linestyle=period2c[boll[0]][2],linewidth=period2c[boll[0]][0],color=period2c[boll[0]][1])
            ax[0].annotate('%d-%d %.1f%%'%(boll[8][9],boll[8][2],100*(boll[4]-boll[5])/boll[5]),xy=(240-2*boll[8][9],y),xytext=(20,offy), textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",
            connectionstyle="angle,angleA=0,angleB=90,rad=10"),fontsize='large',fontweight='bold',color=period2c[boll[0]][1])                
            offy += 20
    bottom,top = ax[0].get_ylim()
    ax[0].broken_barh([(0,15)], (bottom,top-bottom),facecolor='blue',alpha=0.05)                

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
    K[K==0] = 1
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
        "监视":[muti_monitor],            
        "上榜分类":getDTop('90',3)[:10],
        "上榜概念":getDTop('91',15)[:20],
        "ETF":ETFs,
        "自选":BCs,
        "关注":[favoriteList]
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
    return False,(0,0,0,0,0,0)
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
            return zfn>jcn,(N,minv,maxv,real_minv,real_maxv,zfn) #(通道底，通道顶，通道最小值，通道最大值)
    return False,(0,0,0,0,0,0)
"""
boll通道由平直到打开返回True,否则返回False
通道检查n个点，通道宽度都要小于p
"""
def bollopenk(k,period=240,n=16):
    if len(k)>n and k[-1]>k[-2] and k[-1]>k[-3] and k[-1]>k[-4]: #快速过滤掉大部分的
        b,(N,up,down,minv,maxv,real_minv,real_maxv,zfn)=bollwayex(k[:-1],n)
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
def moniter_loop(periods=[15,30,60,240]):
    t = datetime.today()
    ename = 'event%d%d'%(t.month,t.day)
    if not stock.isTransTime():
        b,E = shared.fromRedis(ename)
        return E
    
    companys = xueqiu.get_company_select()
    K = {}
    D = {}    
    for period in periods:
        K[period],D[period] = xueqiu.get_period_k(period)
    b,E = shared.fromRedis(ename)
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
                add('bollopen',companys[i][1],period)
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
                add('maclose',companys[i][1],p[2])
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
    event['timestamp'] = t
    E['event'].append(event) #将E保存
    shared.toRedis(E,ename,ex=7*24*3600)
    return E

def timesplitEvent():
    t = datetime.today()
    E = moniter_loop()
    companys = xueqiu.get_company_select()
    code2c = {}
    for c in companys:
        code2c[c[1]] = c
    result = []
    for es in [('bollopen','通道打开'),('maclose','三角整理')]:
        if es[0] in E:
            for e in E[es[0]].items():
                code = e[0]
                for c in e[1].items():
                    period = c[0]
                    tim = c[1]
                    if tim.hour==t.hour:
                        name = code2c[code][2]
                        result.append(("'%s'周期%d%s"%(name,period,es[1]),es[0],code,period))

    events = E['event']
    for event in events:
        tim = event['timestamp']
        if tim.hour==t.hour:
            for es in [('highup','高开'),('fastup','快速上涨'),('fl_topup','上分类榜'),('gn_topup','上概念榜')]:
                if es[0] in event:
                    for code in event[es[0]]:
                        name = code2c[code][2]
                        result.append(("%d:%d'%s'%s"%(tim.hour,tim.minute,name,es[1]),es[0],code,0))
    return result
            
"""
"""
def monitor():
    toolbar_output = widgets.Output()
    kline_output = widgets.Output()
    event_output = widgets.Output()
    """
    fltopDropdown = widgets.Dropdown(
        options=[],
        value=None,
        description='分类榜',
        disabled=False,
        layout=Layout(width='196px')
    )
    gltopDropdown = widgets.Dropdown(
        options=[],
        value=None,
        description='概念榜',
        disabled=False,
        layout=Layout(width='196px')
    )     
    bollupDropdown = widgets.Dropdown(
        options=[],
        value=None,
        description='通道开',
        disabled=False,
        layout=Layout(width='196px')
    )
    triangleDropdown = widgets.Dropdown(
        options=[],
        value=None,
        description='三角整理',
        disabled=False,
        layout=Layout(width='196px')
    ) 
    highupDropdown = widgets.Dropdown(
        options=[],
        value=None,
        description='高开',
        disabled=False,
        layout=Layout(width='196px')
    )
    fastupDropdown = widgets.Dropdown(
        options=[],
        value=None,
        description='快速上涨',
        disabled=False,
        layout=Layout(width='196px')
    )
    
    box = Box(children=[fltopDropdown,gltopDropdown,triangleDropdown,highupDropdown,fastupDropdown],layout=box_layout)
    """
    currentEventList=None
    checktable = {'bollopen':True,'maclose':False,'highup':True,'fastup':True,'fl_topup':True,'gn_topup':True}
    box = Box(children=[],layout=box_layout)
    def onkline(e):
        #kline_output.clear_output(wait=True)
        with kline_output:
            if e.event[1]=='maclose':
                period = 'd'
                #e.event[3] 代表均线
            else:
                if e.event[3]==240 or e.event[3]==0:
                    period = 'd'
                else:
                    period = e.event[3]
            K(e.event[2],period)
    def updateeventtable():
        nonlocal checktable,currentEventList
        items = []
        if currentEventList is not None:
            for event in currentEventList: #(0描述,1type,2code,3period)
                if checktable[event[1]] and event[2][0]=='B':
                    but = widgets.Button(
                        description=event[0],
                        disabled=False,
                        button_style='',
                        layout=Layout(width='196px'))
                    but.event = event
                    but.on_click(onkline)
                    items.append(but)
        box.children = items

    def loop():
        nonlocal currentEventList
        currentEventList = timesplitEvent()
        updateeventtable()
        xueqiu.setTimeout(60,loop,'monitor.loop')
    loop()
    def oncheck(e):
        nonlocal checktable
        checktable[e['owner'].event] = e['new']
        updateeventtable()
    toolitem = []
    for it in [('通道打开','bollopen'),('三角整理','maclose'),('高开','highup'),('快速上涨','fastup'),('分类上榜','fl_topup'),('概念上榜','gn_topup')]:
        check = widgets.Checkbox(value=checktable[it[1]],description=it[0],disabled=False,layout=Layout(display='block',width='96px'))
        check.event = it[1]
        check.observe(oncheck,names='value')
        toolitem.append(check)
    clearbut = widgets.Button(
                description="清除",
                disabled=False,
                button_style='')
    
    def on_clear(e):
        kline_output.clear_output()
    clearbut.on_click(on_clear)
    toolitem.append(clearbut)    
    checkbox = Box(children=toolitem,layout=box_layout)
    event_output.clear_output(wait=True)
    with event_output:
        display(checkbox,box)  
 
    display(toolbar_output,kline_output,event_output)

"""
返回当前监控的全部boll通道
"""
def bolltrench():
    companys = xueqiu.get_company_select()
    bolls = {}
    t = datetime.today()
    ename = 'bolls'
    b,bolls = shared.fromRedis(ename)
    if not b:
        bolls = {}
    isupdate = False
    for period in [5,15,30,60,240]:
        if period not in bolls or t-bolls[period] > timedelta(minutes=period):
            bolls[period] = t
            isupdate = True
            K,D = xueqiu.get_period_k(period)
            for i in range(len(companys)):
                for j in range(-3,-16,-1): #最后3根k线不参与通道的产生
                    b,(n,down,up,mink,maxk,zfn) = bollwayex(K[i,:j],16,3)
                    if b:
                        tbi = D[j-n][0]
                        tei = D[j][0]
                        if companys[i][1] not in bolls:
                            bolls[companys[i][1]] = []
                        bls = bolls[companys[i][1]]
                        isexist=False
                        for i in range(len(bls)):
                            if bls[i][1]==period: #已经存在就
                                bls[i] = (D[-1][0],period,n,up,down,mink,maxk,tbi,tei,zfn)
                                isexist = True
                                break
                        if not isexist:
                            bls.append((D[-1][0],period,n,up,down,mink,maxk,tbi,tei,zfn))
                        break
    if isupdate:
        shared.toRedis(bolls,ename,ex=3*24*3600)
    return bolls

"""
向上通道突破
bolls = [(0 period,1 price,2 tbi,3 tei,4 top,5 bottom),...]
"""
def BollK(code,bolls,isall=True):
    def getx(d,b,e):
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
    period2c = {5:(3,'forestgreen','dotted'),15:(3,'royalblue','dotted'),30:(3,'fuchsia','dashed'),60:(4,'darkorange','dashdot'),240:(5,'red','dotted')}
    style = (('5日','magenta',1),('10日','orange',3))
    period2ma = {5:(320,640,0,1),15:(160,320,0,1),15:(80,160,0,1),30:(40,80,0,1),60:(20,40,0,1),120:(10,20,0,1),'d':(5,10,0,1)}
    def cb(self,axs,bi,ei):
        axK = axs[0]
        for bo in bolls:
            bbi,bei = getx(self._date,bo[2],bo[3])
            if bbi==0:
                continue
            if bei==0:
                bei = ei-3
            if bei>bi and bei-bbi>0:
                axK.broken_barh([(bbi,bei-bbi)], (bo[5],bo[4]-bo[5]),facecolor='None',edgecolor=period2c[bo[0]][1],linewidth=period2c[bo[0]][0],linestyle=period2c[bo[0]][2])
        #绘制5日和10日均线
        m = period2ma[self._period]
        xx,alv = stock.maRangeK(self._k,m[0],bi,ei)
        axK.plot(xx,alv,label=style[m[2]][0],color=style[m[2]][1],linewidth=style[m[2]][2])
        xx,alv = stock.maRangeK(self._k,m[1],bi,ei)
        axK.plot(xx,alv,label=style[m[3]][0],color=style[m[3]][1],linewidth=style[m[3]][2])            

    period = 0
    for bo in bolls:
        period = max(period,bo[0])
    if period==240:
        period = 'd'
    if isall:
        kline.Plote(code,period,config={'main_menu':'CLEAR','index_menu':'FLOW','index':False,'cb':cb},mode='normal').show(figsize=(36,15))
    else:
        kline.Plote(code,period,config={'main_menu':'CLEAR','index_menu':'FLOW','index':False,'cb':cb},mode='normal').showKline(figsize=(16,16))

"""
通道突破监控
"""
def monitor_bollup():
    monitor_output = widgets.Output()
    kline_output = widgets.Output()
    kview_output = widgets.Output()
    bollup_output = widgets.Output()    
    prefix_checktable = {'90':True,'91':False,'0':False,'1':False,'2':False}
    peroid_checktable = {5:True,15:True,30:True,60:True,240:True}    
    companys = xueqiu.get_company_select()
    code2com = xueqiu.get_company_code2com()
    ALLBOLLS = []
    FILTERCOLORS = []
    FILTERCURRENT = []
    npage = 0
    page = 0
    switch = 1
    news = 1 #0 持续 ，1 最新 ，2 全部
    tf = 0 #时间过滤
    def tf2range():
        nonlocal tf
        if tf==0:
            t = datetime.today()
            return (t.hour*60-(60-t.minute),t.hour*60+60)
        elif tf==1:
            return 9*60,9*60+30
        elif tf==2:
            return (9*60+30,11*60+30)
        elif tf==3:
            return (13*60,15*60)
        else:
            return (0,15*60)
    def onkline(e):
        kline_output.clear_output(wait=True)
        with kline_output:
            if e.event[0]=='bollup':
                BollK(e.event[1][1],e.bolls,True)

    def update_bollupbuttons():
        nonlocal ALLBOLLS,FILTERCOLORS,FILTERCURRENT,switch,news
        
        bos = bolltrench()
        t = date.today()
        b,k,d = xueqiu.getTodayRT()
        t2 = t
        if not b:
            for i in range(1,7):
                t2 = t-timedelta(days=i)
                b,k,d = xueqiu.getTodayRT(t2)
                if b:
                    break
                if i==6:
                    return
        #使用昨天的k,d数据
        b1,ky,dy = False,None,None
        for i in range(1,7):
            b1,ky,dy = xueqiu.getTodayRT(t2-timedelta(days=i))
            if b1:
                break
        ALLBOLLS = []
        FILTERCOLORS = []
        
        items = []
        for i in range(len(companys)):
            code = companys[i][1]
            if code in bos:
                isnew = False #和昨天比
                bolls = []
                periods = []
                for bo in bos[code]:
                    #最近股价要大于通道顶，同时要大于通道里面的全部k线
                    #bo (0 timestramp,1 period,2 n,3 up,4 down,5 mink,6 maxk,7 tbi,8 tei,9 zfn)
                    if companys[i][3] in prefix_checktable and prefix_checktable[companys[i][3]] and bo[1] in peroid_checktable and peroid_checktable[bo[1]]:
                        H = bo[6]-bo[5]
                        if switch==1: #突破向上
                            if k[i,-1,0] > bo[6]:
                                periods.append(bo[1])
                                isnew = b1 and (ky[i,-1,0] < bo[6])
                                bolls.append((bo[1],k[i,-1,0],bo[7],bo[8],bo[3],bo[4],isnew,'up',bo)) #,(0 period,1 price,2 tbi 3 tei,4 up 5 down ,6 isnew今天新的, 7 类型up,top...,8 bo)
                        elif switch==2: #通道顶部
                            if k[i,-1,0] > bo[5]+2*H/3 and k[i,-1,0] < bo[6]:
                                periods.append(bo[1])
                                isnew = b1 and (ky[i,-1,0] > bo[5]+2*H/3 and ky[i,-1,0] < bo[6])
                                bolls.append((bo[1],k[i,-1,0],bo[7],bo[8],bo[3],bo[4],isnew,'top',bo))
                        elif switch==3: #通道内部
                            if k[i,-1,0] <= bo[6] and k[i,-1,0] >= bo[5]:
                                periods.append(bo[1])
                                isnew = b1 and (ky[i,-1,0] < bo[5]+2*H/3 and ky[i,-1,0] > bo[5]+H/3)
                                bolls.append((bo[1],k[i,-1,0],bo[7],bo[8],bo[3],bo[4],isnew,'mid',bo))
                        elif switch==4: #通道底部
                            if k[i,-1,0] < bo[5]+H/3 and k[i,-1,0] > bo[5]:
                                periods.append(bo[1])
                                isnew = b1 and (ky[i,-1,0] < bo[5]+H/3 and ky[i,-1,0] > bo[5])
                                bolls.append((bo[1],k[i,-1,0],bo[7],bo[8],bo[3],bo[4],isnew,'bottom',bo))
                        else: #底部向下
                            if k[i,-1,0] < bo[5]:
                                periods.append(bo[1])
                                isnew = b1 and (ky[i,-1,0] < bo[5])
                                bolls.append((bo[1],k[i,-1,0],bo[7],bo[8],bo[3],bo[4],isnew,'down',bo))
                if len(bolls)>0 and ((news==1 and isnew) or (news==0 and not isnew)) or news==2:
                    bstyle = ''
                    if k[i,-1,3]+k[i,-1,4]>0 and k[i,-1,6]<0:
                        bstyle = 'danger'
                    elif k[i,-1,3]+k[i,-1,4]>0:
                        bstyle = 'warning'
                    elif k[i,-1,3]+k[i,-1,4]<0 and k[i,-1,6]>0:
                        bstyle = 'success'
                    but = widgets.Button(
                        description="%s%%%s%s"%(k[i,-1,1],companys[i][2],str(periods)),
                        disabled=False,
                        button_style=bstyle,
                        icon='cannabis',
                        layout=Layout(width='240px'))
                    but.event = ('bollup',companys[i],periods)
                    but.bolls = bolls
                    but.code = companys[i][1]
                    ALLBOLLS.append((companys[i],bolls,i,k[i,-1,1]))
                    but.on_click(onkline)
                    items.append((k[i,-1,1],but,companys[i][1]))
        """
        上面的算法对当前通道进行搜索，返回ALLBOLLS,和满足条件的公司对应的按钮列表items
        bolls = [(0 period,1 price,2 tbi 3 tei,4 up 5 down ,6 isnew今天新的, 7 类型up,top...,8 bo),...]
        ALLBOLLS = [
            (0 company,1 bolls,2 i公司在companys中的序号,3 检查成功的涨幅),...
        ]
        """                    
        """
        返回第一个达到条件的点
        """
        def get_breakpt(k,d,bos):
            r = []
            for b in bos:
                bo = b[8]
                H = bo[6]-bo[5]
                for i in range(len(k)):
                    if d[i]>bo[8]: #监测点时间必须大于通道结尾的时间
                        if b[7]=='up':
                            if k[i]>bo[6]:
                                r.append((i,b[0]))
                                break
                        elif b[7]=='down':
                            if k[i]<bo[5]:
                                r.append((i,b[0]))
                                break                            
                        elif b[7]=='top':
                            if k[i] > bo[5]+2*H/3 and k[i] < bo[6]:
                                r.append((i,b[0]))
                                break                            
                        elif b[7]=='bottom':
                            if k[i] < bo[5]+H/3 and k[i] > bo[5]:
                                r.append((i,b[0]))
                                break                            
                        elif b[7]=='mid':
                            if k[i] < bo[5]+2*H/3 and k[i] > bo[5]+H/3:
                                r.append((i,b[0]))
                                break                            
            return r
        """
        将ALLBOLLS中的公司绘制出价格走势图表，并且标记出突破点的价格和周期
        """      
        ALLBOLLS = sorted(ALLBOLLS,key=lambda it:it[3],reverse=True)
        tfr = tf2range()
        FILTERCURRENT = []
        for c in ALLBOLLS:
            bptxs = get_breakpt(k[c[2],:,0],d,c[1])
            isd = False
            for bp in bptxs:
                tt = d[bp[0]].hour*60+d[bp[0]].minute
                if tt>=tfr[0] and tt<=tfr[1]:
                    isd = True
            if isd:
                FILTERCURRENT.append((c,bptxs))
                FILTERCOLORS.append(c[0][1])

        """
        下面对按钮对应公司的日涨幅进行排序，将涨幅大的放置在列表的前面        
        """
        sorteditems = sorted(items,key=lambda it:it[0],reverse=True)
        items = []
        for it in sorteditems:
            if it[2] in FILTERCOLORS:
                items.append(it[1])
        bollup_output.clear_output(wait=True)
        with bollup_output:
            display(Box(children=items,layout=box_layout))        
        update_current_plot(k,d)      
    """
    绘制更新选择的分时图表
    """
    def update_current_plot(k=None,d=None):
        nonlocal FILTERCURRENT,monitor_output,page,npage,pagedown,pageup
        if k is None: #如果k,d没有传递过来
            t = date.today()
            b,k,d = xueqiu.getTodayRT()
            t2 = t
            if not b:
                for i in range(1,7):
                    t2 = t-timedelta(days=i)
                    b,k,d = xueqiu.getTodayRT(t2)
                    if b:
                        break
                    if i==6:
                        return            
        N = len(FILTERCURRENT)
        npage = int(N/8.)+(0 if N%8==0 else 1)
        if page>=npage:
            page = npage-1
        if page>=npage-1:
            pagedown.disabled = True
        else:
            pagedown.disabled = False
        if page<0:
            page = 0
        if page<=0:
            pageup.disabled = True
        else:
            pageup.disabled = False

        gs_kw = dict(width_ratios=[1,1,1,1], height_ratios=[2,1,2,1])
        fig,axs = plt.subplots(4,4,figsize=(32,16),gridspec_kw = gs_kw)
        views = []
        for i in range(8*page,N):
            c = FILTERCURRENT[i][0]
            x = 2*int((i-8*page)/4.)
            y = (i-8*page)%4
            if x<3:
                ax = [axs[x,y],axs[x+1,y]]
                views.append(c[0][1])
                plotfs(ax,k[c[2],:,:],d,c[0][2],bolls=c[1])
        """
        for item in box.children:
            if item.code in views:
                item.icon = 'check'
            else:
                item.icon = ''
        """
        fig.subplots_adjust(hspace=0,wspace=0.08)
        kline.output_show(monitor_output)

    def on_perfixcheck(e):
        nonlocal prefix_checktable
        prefix_checktable[e['owner'].it] = e['new']
        update_bollupbuttons()
    def on_peroidcheck(e):
        nonlocal peroid_checktable
        peroid_checktable[e['owner'].it] = e['new']
        update_bollupbuttons()       
    switch2name = {1:'向上突破',2:'通道上部',3:'通道内部',4:'通道下部',5:'向下突破'}
    switchname2switch = {'向上突破':1,'通道上部':2,'通道内部':3,'通道下部':4,'向下突破':5}
    switchDropdown = widgets.Dropdown(
        options=['向上突破','通道上部','通道内部','通道下部','向下突破'],
        value=switch2name[switch],
        description='',
        disabled=False,
        layout=Layout(width='96px')
    ) 
    def on_switch(e):
        nonlocal switch
        switch = switchname2switch[e['new']]
        update_bollupbuttons()
    switchDropdown.observe(on_switch,names='value')
    checkitem = [switchDropdown]
    for it in [('分类','90'),('概念','91'),('SH','1'),('SZ','0'),('ETF','2')]:
        check = widgets.Checkbox(value=prefix_checktable[it[1]],description=it[0],disabled=False,layout=Layout(display='block',width='72px'))
        check.it = it[1]
        check.observe(on_perfixcheck,names='value')
        checkitem.append(check)
    for it in [('5',5),('15',15),('30',30),('60',60),('240',240)]:
        check = widgets.Checkbox(value=peroid_checktable[it[1]],description=it[0],disabled=False,layout=Layout(display='block',width='72px'))
        check.it = it[1]
        check.observe(on_peroidcheck,names='value')
        checkitem.append(check)
    """
    对突破进行过滤
    0 持续:昨天已经突破，今天还在突破位置
    1 最新:昨天没有突破，今天突破的
    2 昨日:昨日突破，今日回落的(目前没有实现)
    """
    new2name = {0:'持续',1:'最新',2:'全部'}
    newname2new = {'持续':0,'最新':1,'全部':2}
    def on_news(e):
        nonlocal news
        news = newname2new[e['new']]
        update_bollupbuttons()
    newdrop =  widgets.Dropdown(
        options=['最新','持续','全部'],
        value=new2name[news],
        description='',
        disabled=False,
        layout=Layout(width='96px')
    ) 
    checkitem.append(newdrop)
    newdrop.observe(on_news,names='value')
    """
    时序过滤
    0 当前:最近一个小时突破的
    1 盘前:开盘前发生突破
    2 10点中之前
    """

    tf2name = {0:'最近',1:'盘前',2:'上午',3:'下午',4:'全天'}
    name2tf = {'最近':0,'盘前':1,'上午':2,'下午':3,'全天':4}
    tfdrop = widgets.Dropdown(
        options=['最近','盘前','上午','下午','全天'],
        value=tf2name[tf],
        description='',
        disabled=False,
        layout=Layout(width='96px')
    )
    def on_tf(e):
        nonlocal tf
        tf = name2tf[e['new']]
        update_bollupbuttons()        
    checkitem.append(tfdrop)
    tfdrop.observe(on_tf,names='value')

    def on_clear(e):
        kline_output.clear_output()
        kview_output.clear_output()
    clearbut = widgets.Button(
                description="清除",
                disabled=False,
                button_style='')
    clearbut.on_click(on_clear)
    checkitem.append(clearbut)
    
    def on_list(e):
        nonlocal ALLBOLLS,FILTERCOLORS
        kline_output.clear_output()
        with kline_output:
            for bo in ALLBOLLS:
                if bo[0][1] in FILTERCOLORS:
                    BollK(bo[0][1],bo[1])
        
    allbut = widgets.Button(
                description="全列",
                disabled=False,
                button_style='')
    allbut.on_click(on_list)
    checkitem.append(allbut)
    def on_pagedown(e):
        nonlocal page,npage
        page+=1
        if page>=npage:
            page = npage-1     
        update_current_plot()   
    pagedown = widgets.Button(
                description="下一页",
                disabled=False,
                button_style='')
    pagedown.on_click(on_pagedown)
    
    def on_pageup(e):
        nonlocal page,npage
        page-=1
        if page<0:
            page = 0
        update_current_plot()
    pageup = widgets.Button(
                description="上一页",
                disabled=False,
                button_style='')
    pageup.on_click(on_pageup)
    checkitem.append(pageup)
    checkitem.append(pagedown)

    def loop():
        update_bollupbuttons()
        xueqiu.setTimeout(60,loop,'monitor.bollup')
    loop()    
    checkbox = Box(children=checkitem,layout=box_layout)
    #mbox = Box(children=[monitor_output,kview_output],layout=Layout(display='flex',flex_flow='row',align_items='stretch',min_width='3048px'))
    display(monitor_output,checkbox,bollup_output,kline_output)

"""
返回资金流入最稳定
typeid=0资金流,1增长流,2增长排名
"""
def get_strong_flow(k,d,companys,prefix='90',typeid=0):
    S = []
    if typeid==2:
        for i in range(k.shape[0]):
            if companys[i][3]==prefix:
                S.append((k[i,-1,1],i))
    else:
        for i in range(k.shape[0]):
            if companys[i][3]==prefix:
                mflow = k[i,:,3]+k[i,:,4]
                inn = 1
                outn = 1
                for j in range(1,k.shape[1]):
                    if typeid==0:
                        if mflow[j]>mflow[j-1]:
                            inn+=1
                        else:
                            outn+=1
                    elif typeid==1:
                        if k[i,j,1]>k[i,j-1,1]:
                            inn+=1
                        else:
                            outn+=1                    
                S.append((inn/outn,i))
    S = sorted(S,key=lambda it:it[0],reverse=True)
    R = []
    for s in S:
        R.append(s[1])
    return R
"""
分屏多窗口监控分时图
"""
def muti_monitor():
    monitor_output = widgets.Output()
    companys = xueqiu.get_company_select()
    code2i = xueqiu.get_company_code2i()
    shi = code2i['SH000001']
    szi = code2i['SZ399001']
    def update_plot(data,row=4,col=7,figsize=(50,16)):
        gs_kw = dict(height_ratios=[2,1,2,1])
        fig,axs = plt.subplots(row,col,figsize=figsize,gridspec_kw = gs_kw)
        for i in range(int(row*col/2)):
            if i<len(data):
                p = data[i]
                x = 2*int((i)/col)
                y = (i)%col
                ax = [axs[x,y],axs[x+1,y]]
                plotfs(ax,p[0],p[1],p[2])
        fig.subplots_adjust(hspace=0,wspace=0.08)
        kline.output_show(monitor_output)
    def loop():
        nonlocal companys,shi,szi
        t = date.today()
        b,k,d = xueqiu.getTodayRT()
        t2 = t
        if b:
            data = [(k[shi,:,:],d,companys[shi][2]),(k[szi,:,:],d,companys[szi][2])]
            R = []
            for it in (('2',2,'ETF'),('90',0,'行业资金'),('90',2,'行业增幅'),('91',0,'概念资金'),('91',2,'概念增幅')):    
                S = get_strong_flow(k,d,companys,it[0],it[1])
                for i in S[:3]:
                    if i not in R:
                        data.append((k[i,:,:],d,'%s %s'%(companys[i][2],it[2])))
                        R.append(i)
            update_plot(data)
        xueqiu.setTimeout(60,loop,'monitor.monitor')
    loop() 
    display(monitor_output)