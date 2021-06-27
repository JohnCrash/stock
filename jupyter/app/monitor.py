from ipywidgets.widgets.widget_selection import Dropdown
from ipywidgets import GridBox
from IPython.display import display,Markdown
from IPython.core.interactiveshell import InteractiveShell
import ipywidgets as widgets
from ipywidgets import Layout, Button, Box
from datetime import date,datetime,timedelta
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import math
import time
import numpy as np
import random
from numpy.core.fromnumeric import compress
from numpy.core.numeric import NaN
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
mycolors=[
    "red",
    "purple",    
    "black",
    "green",
    "blue",
    "brown",
    "orangered",
    "sienna",
    "darkorange",
    "goldenrod",
    "olivedrab",
    "olive",
    "darkgreen",
    "seagreen",
    "teal",
    "darkturquoise",
    "steelblue",
    "dodgerblue",
    "slategrey",
    "royalblue",
    "mediumblue",
    "blueviolet",
    "magenta",
    "crimson",
    "pink",
    "cyan"
]
name2int = {}
namecount = 0
random.seed()
def getmycolor(name):
    global mycolors,name2int,namecount
    if name in name2int:
        return mycolors[name2int[name]]
    
    name2int[name] = random.randint(0,len(mycolors)-1)#namecount%len(mycolors)
    namecount += 1
    return mycolors[name2int[name]]
"""
绘制分时图
ax 绘制句柄数组,k (),d 日期,title 标题,style绘制风格
ma5b 5日均线起点
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
def plotfs(ax,k,d,title,bolls=None,style=defaultPlotfsStyle,ma5b=None,topshow=None):
    ax[0].set_title(title,y=0.93)
    x = np.arange(k.shape[0])
    xticks = [0,60-15,2*60-15,3*60+15,4*60+15,len(d)-1]
    ax[0].axhline(y=0,color='black',linestyle='dotted')
    ax[0].plot(x,k[:,1],color=style['pcolor'])
    m60 = stock.ma(k[:,1],60)
    ax[0].plot(x,m60,color=style['ma60color'],linestyle=style['ma60linestyle'])#分时均线
    #计算盘前开始于结束
    pbi = 0
    for i in range(len(d)-1,0,-1):
        if d[i].hour==9 and d[i].minute==29:
            ax[0].scatter([i],[k[i,1]])
        if d[i].hour==9 and (d[i].minute==15 or d[i].minute==16):
            pbi=i
            break
    
    if ma5b is not None and len(k)>0:
        openp = k[-1,0]/(1.+k[-1,1]/100.)
        ma5 = np.zeros((len(k),))
        for i in range(len(k)):
            if i<15:
                ma5[i] = ma5b
            else:
                ma5[i] = ma5[i-1]+(k[i,0]-ma5[i-1])/(240*5) #这是一个近似迭代
        
        ax[0].plot(x,100*(ma5-openp)/openp,linewidth=4,color='magenta')
    if topshow is not None:
        xx = 0
        for i in range(len(d)):
            if d[i] == topshow[1]:
                xx = i
                yy = k[i,1]
        if xx!=0:
            ax[0].annotate(str(topshow[0]),xy=(xx,yy),xytext=(-30,50), textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=90,rad=10"),fontsize='large',fontweight='bold')
    if len(ax)==2:
        ax[1].axhline(y=0,color='black',linestyle='dotted')
        ax[1].plot(x,k[:,3]+k[:,4],color=style['maincolor']) #主力
        ax[1].plot(x,k[:,6],color=style['tingcolor']) #散
        ax[1].set_xlim(0,15+4*60)
        ax[1].set_xticks(xticks)
        ax[1].xaxis.set_major_formatter(MyFormatterRT(d,'d h:m'))
        bottom,top = ax[1].get_ylim()
        ax[1].broken_barh([(pbi,15)], (bottom,top-bottom),facecolor='blue',alpha=0.1)    
    else:
        ax[0].xaxis.set_major_formatter(MyFormatterRT(d,'d h:m'))
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
    ax[0].broken_barh([(pbi,15)], (bottom,top-bottom),facecolor='blue',alpha=0.1) 

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
def K(code,period=None,pos=None,mode='auto'):
    if pos is None:
        kline.Plote(code,period,config={'index':True},mode=mode).show(figsize=(46,20))
    else:
        kline.Plote(code,period,config={'index':True},mode=mode,lastday=10*365).show(pos=pos)

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

def getma5longtop():
    companys = xueqiu.get_company_select()
    K,D = xueqiu.get_period_k(30)
    MA5 = stock.maMatrix(K,40)
    R = []
    for j in range(len(companys)):
        n = 0
        m = 0
        for i in range(-1,-len(D),-1):
            if K[j,i]>MA5[j,i]:
                n+=1
                m=0
            else:
                m+=1
            if m>8:
                break
        if n>0:
            R.append((j,i,n))
    return sorted(R,key=lambda it:it[2],reverse=True)

"""
将概念的中的个股进行5日线长度排名
下5日线超过1天就算下5日线
"""
def getma5longtopgn(code):
    af = stock.dateString(datetime.today()-timedelta(days=60))
    QS = stock.query("select code from emlist where emcode='%s'"%code)            
    R = []
    for it in QS:
        c,k,d = stock.loadKline(it[0],5,after=af)
        if len(k)>0:
            MA5 = stock.maK(k,240)
            n = 0
            m = 0
            for i in range(-1,-len(MA5),-1):
                if k[i,4]>MA5[i]:
                    n+=1
                    m=0
                else:
                    m+=1
                if m>8*6:
                    break
            if n>0:
                R.append((c,i,n))
    return sorted(R,key=lambda it:it[2],reverse=True)
"""
一个5日均线长度排行榜
如果全天都在5日线下就算结束
"""
def ma5longTop():
    tools = []
    companys = xueqiu.get_company_select()
    tops = getma5longtop()
    plot_output = widgets.Output()
    complot_output = widgets.Output()
    list_output = widgets.Output()
    combox = Box(children=[],layout=box_layout)
    cur_prefix = ''
    def listtops(prefix,r):
        nonlocal list_output,tops,companys
        list_output.clear_output()
        with list_output:
            for it in tops:
                com = companys[it[0]]
                n = math.ceil(it[2]/8)
                if com[3]==prefix and n>=1 and n>=r[0] and n<r[1]:
                    K(com[1],mode='normal')
    def on_gntops(e): #对概念内进行排行
        complot_output.clear_output()
        list_output.clear_output()
        gntops = getma5longtopgn(e.code)
        R = []
        for it in gntops:
            if it[2]>=48:
                R.append((it[2],it[0][2],it[0][1]))
        with complot_output:
            fig,ax = plt.subplots(1,1,figsize=(46,16))
            x = np.arange(len(R))
            ax.set_xticks(x)
            ax.set_xticklabels([it[1] for it in R])
            plt.setp(ax.get_xticklabels(),rotation=45,horizontalalignment='right')
            ax.set_xlim(-1,len(R))
            ax.bar(x,[math.ceil(it[0]/48.) for it in R],0.9)
        kline.output_show(complot_output)
        with list_output:
             K(e.code,mode='normal')
             #前20
             for i in range(len(gntops)):
                 if i<20:
                    K(gntops[i][0][1],mode='normal')

    def plotetops(prefix):
        nonlocal plot_output,tops,companys,cur_prefix,combox
        R = []
        cur_prefix = prefix
        buts = []
        for it in tops:
            com = companys[it[0]]
            if com[3]==prefix and it[2]>=8:
                R.append((it[2],com[2],com[1]))
                buts.append(widgets.Button(description="%s%d"%(com[2],math.ceil(it[2]/8))))
                buts[-1].code = com[1]
                buts[-1].on_click(on_gntops)
        combox.children = buts
        plot_output.clear_output()
        with plot_output:
            fig,ax = plt.subplots(1,1,figsize=(46,16))
            x = np.arange(len(R))
            ax.set_xticks(x)
            ax.set_xticklabels([it[1] for it in R])
            plt.setp(ax.get_xticklabels(),rotation=45,horizontalalignment='right')
            ax.set_xlim(-1,len(R))
            ax.bar(x,[math.ceil(it[0]/8.) for it in R],0.9)
        kline.output_show(plot_output)
    def on_click(e):
        plotetops(e.prefix)

    for it in [('概念','91'),('行业','90'),('ETF','2'),('SH','1'),('SZ','0')]:
        tools.append(widgets.Button(description=it[0]))
        tools[-1].prefix = it[1]
        tools[-1].on_click(on_click)
    def on_rangelist(e):
        nonlocal cur_prefix
        listtops(cur_prefix,e.range)

    for it in [(20,1000,'大于20'),(10,20,'10-20'),(5,10,'5-10'),(1,5,'1-5')]:
        tools.append(widgets.Button(description=it[2]))
        tools[-1].range = (it[0],it[1])
        tools[-1].on_click(on_rangelist)
    tool_box = Box(children=tools,layout=box_layout)
    display(tool_box,plot_output,combox,complot_output,list_output)
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

def getCrossMa(prefix='91',mas=[5,20],nday=1):
    companys = xueqiu.get_company_select()
    K,D = xueqiu.get_period_k(240)
    maks = []
    for ma in mas:
        maks.append(stock.maMatrix(K,ma))
    R = []
    for i in range(len(companys)):
        b = True
        for j in range(len(mas)):
            if K[i,-nday-1]>maks[j][i,-nday-1]:
                b = False
                break
        if b:
            for j in range(len(mas)):
                if K[i,-1]<maks[j][i,-1]:
                    b = False
                    break
            if b:
                R.append(companys[i][1])
    return R
"""
返回可做的概念或者分类
10点钟在排行榜上
"""
def get10Top(prefix='90',top=5,nday=3,eit=None,detail=False,reverse=True):
    companys = xueqiu.get_company_select()
    K,D = xueqiu.get_period_k(30)
    n = 0
    R = {}
    ei = -1
    if eit is not None:
        for i in range(-1,-len(D),-1):
            if D[i][0]<=eit:
                ei = i
                break
    for i in range(ei,-len(D),-1):
        if n<nday:
            if D[i][0].hour==10 and D[i][0].minute==0:
                n+=1
                m=0
                K[K[:,i-2]==0,i-2] = 1
                dk = (K[:,i]-K[:,i-2])/K[:,i-2]
                a = list(np.argsort(dk))
                a.reverse()
                if type(prefix)==str:
                    for j in a:
                        if m<top:
                            if companys[j][3]==prefix and K[j,i]>K[j,i-2]: #附加一个条件最高价必须大于昨日收盘
                                if companys[j][1] not in R:
                                    R[companys[j][1]] = (j,i,D[i][0],m+1)
                                    m+=1
                        else:
                            break
                else:
                    for j in a:
                        if m<top:
                            if companys[j][1] in prefix and K[j,i]>K[j,i-2]:
                                if companys[j][1] not in R:
                                    R[companys[j][1]] = (j,i,D[i][0],m+1)
                                    m+=1
                        else:
                            break
        else:
            break
    """
    删除已经走坏的分类
    1.全天50%处于5日均线下方
    """
    for it in list(R.items()):
        j = it[1][0]
        i = it[1][1]
        ma5 = stock.ma(K[j,:],40)
        n = 0
        for s in range(ei,i-1,-1): #如果有连续的4根k线在5日均线下就算走坏
            if K[j,s] < ma5[s]:
                n+=1
            else:
                n = 0
            if n>=4:
                del R[it[0]]
                break
    """
    进行排序
    """
    result = []
    for it in sorted(R.items(),key=lambda it:it[1][2],reverse=reverse):
        if detail:
            result.append((it[0],it[1][2],it[1][3]))
        else:
            result.append(it[0])
    return result
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
网格放置k线图
"""
def gridK(codes,ncol=2):
    outs = []
    for code in codes:
        outs.append(widgets.Output())
        with outs[-1]:
            kline.Plote(code,5,mode='normal').show(figsize=(18,16),simple=True)
    grid = GridBox(children=outs,
        layout=Layout(
            width='100%',
            grid_template_columns='50% 50%')
       )
    display(grid)

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
def newriseview():
    HotPlot().loop()
def Indexs():
    global ETFs,BCs
    menus = {
        "盯盘":[newriseview],
        "横向比较":[riseview],
        "大盘":['SH000001', #上证
            'SZ399001', #深成
            'SZ399006'],#创业        
        "可交易":[muti_monitor],
        "通道突破":[monitor_bollup],
        "活跃分类":get10Top('90',5,3),
        "活跃概念":get10Top('91',10,3),
        "上榜分类":getDTop('90',3)[:10],
        "上榜概念":getDTop('91',15)[:20],
        "5日线排行":[ma5longTop],
        "ETF":ETFs,
        "自选":BCs,
        "关注":[favoriteList]
    }
    indexpage(menus)    
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
    for period in [15,30,60]:
        if period not in bolls or t-bolls[period] > timedelta(minutes=period):
            bolls[period] = t
            isupdate = True
            K,D = xueqiu.get_period_k(period)
            for i in range(len(companys)):
                for j in range(-3,-16,-1): #最后3根k线不参与通道的产生
                    b,(n,mink,maxk,zfn) = stock.bollwayex(K[i,:j])
                    if b:
                        bi,ei,mink,maxk= stock.extway(K[i,:],j,n,mink,maxk)
                        if ei-bi>(4*16*15)/period: #>4 day
                            tbi = D[bi][0]
                            tei = D[ei][0]
                            if companys[i][1] not in bolls:
                                bolls[companys[i][1]] = []
                            bls = bolls[companys[i][1]]
                            isexist=False
                            for i in range(len(bls)):
                                if bls[i][1]==period: #已经存在就
                                    bls[i] = (D[-1][0],period,n,mink,maxk,mink,maxk,tbi,tei,zfn)
                                    isexist = True
                                    break
                            if not isexist:
                                bls.append((D[-1][0],period,n,mink,maxk,mink,maxk,tbi,tei,zfn))
                            break
    if isupdate:
        shared.toRedis(bolls,ename,ex=2*3600)
    return bolls

"""
向上通道突破
bolls = [(0 period,1 price,2 tbi,3 tei,4 top,5 bottom),...]
"""
def BollK(code,bolls,isall=True):
    period2c = {5:(3,'forestgreen','dotted'),15:(3,'royalblue','dotted'),30:(3,'fuchsia','dashed'),60:(4,'darkorange','dashdot'),240:(5,'red','dotted')}
    style = (('5日','magenta',1),('10日','orange',3))
    period2ma = {5:(320,640,0,1),15:(160,320,0,1),15:(80,160,0,1),30:(40,80,0,1),60:(20,40,0,1),120:(10,20,0,1),'d':(5,10,0,1)}
    def cb(self,axs,bi,ei):
        axK = axs[0]
        for bo in bolls:
            bbi,bei = stock.get_date_i(self._date,bo[2],bo[3])
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

    period = 5
    for bo in bolls:
        period = max(period,bo[0])
    if period==240:
        period = 'd'
    if isall:
        kline.Plote(code,period,config={'main_menu':'CLEAR','index_menu':'FLOW','index':False,'cb':cb},mode='normal').show(figsize=(36,15))
    else:
        kline.Plote(code,period,config={'main_menu':'CLEAR','index_menu':'FLOW','index':False,'cb':cb},mode='normal').show(figsize=(18,15),simple=True)#showKline(figsize=(18,16))

"""
返回最近的实时数据
"""
def get_last_rt(t):
    b,k,d = xueqiu.getTodayRT(t)
    t2 = t
    if not b:
        for i in range(1,7):
            t2 = t-timedelta(days=i)
            b,k,d = xueqiu.getTodayRT(t2)
            if b:
                break
    return t2,k,d

_rt_k = None
_rt_d = None
def get_rt(n=1):
    """
    取的最近n天的k,d数据，并且叠加快速更新数据
    """
    global _rt_k,_rt_d
    t = datetime.today()
    K = None
    D = []
    if _rt_k is None:
        for i in range(n):
            pt,k,d = get_last_rt(t)
            if d is not None:
                if K is None:
                    K = k
                else:
                    if k.shape[0]==K.shape[0]:
                        K = np.hstack((k,K))
                    else:
                        k2 = np.zeros((K.shape[0],k.shape[1],k.shape[2]))
                        k2[:k.shape[0],:,:] = k
                        K = np.hstack((k2,K))
                D = d+D
                t = pt-timedelta(days=1)
            else:
                break
    elif t.minute==_rt_d[-1].minute and t.hour==_rt_d[-1].hour: #没有新的1分钟数据
        #完全不需要更新
        K = _rt_k
        D = _rt_d
    else: #重新加装今天的数据
        pt,k,d = get_last_rt(t)
        for i in range(len(d)):
            if d[i]>_rt_d[-1]:
                break
        D = _rt_d+d[i:]
        if k.shape[0]>_rt_k.shape[0]:
            news = np.zeros((k.shape[0],_rt_k.shape[1],_rt_k.shape[2]))
            news[:_rt_k.shape[0]] = _rt_k
            _rt_k = news
        K = np.hstack((_rt_k,k[:,i:,:]))
    if K is not None and stock.isTransTime() and stock.isTransDay() and t.hour==9 and t.minute>=30: #一般数据更新周期1分钟，这里对最后的数据做即时更新
        b,a,ts,rtlist = xueqiu.getEmflowRT9355()
        if b:
            code2i = xueqiu.get_company_code2i()
            for j in range(len(rtlist)):
                c = rtlist[j][2]
                i = code2i[c]
                if i<K.shape[0]:
                    K[i,-1,:] = a[j,-1,:]
    _rt_k = K
    _rt_d = D
    return K,D
"""
通道突破监控
"""
def monitor_bollup():
    monitor_output = widgets.Output()
    kline_output = widgets.Output()
    kview_output = widgets.Output()
    list_output = widgets.Output()    
    list_box = Box(children=[],layout=box_layout)
    prefix_checktable = {'90':False,'91':True,'0':False,'1':False,'2':False}
    peroid_checktable = {5:True,15:True,30:True,60:True,240:False}    
    companys = xueqiu.get_company_select()
    code2i = xueqiu.get_company_code2i()
    #code2com = xueqiu.get_company_code2com()
    ALLBOLLS = []
    FILTERCOLORS = []
    FILTERCURRENT = []
    button_items = []
    flow_xch = {}
    npage = 0
    page = 0
    switch = 1
    news = 2 #0 持续 ，1 最新 ，2 全部
    tf = 4 #时间过滤
    top10 = False #10top过滤,概念或者分类必须在get10Top返回的列表中间
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
        kview_output.clear_output(wait=True)
        with kview_output:
            if e.event[0]=='bollup':
                BollK(e.event[1][1],e.bolls,False)

    def update_bollupbuttons():
        nonlocal ALLBOLLS,FILTERCOLORS,FILTERCURRENT,switch,news,list_output,list_box,button_items,flow_xch,top10
        bos = bolltrench()
        t = date.today()
        t2,k,d = get_last_rt(t)
        #使用昨天的k,d数据
        b1,ky,dy = get_last_rt(t2-timedelta(days=1))
        ALLBOLLS = []
        FILTERCOLORS = []
        dt5 = timedelta(minutes=5)
        for i in list(flow_xch.keys()):
            if t-flow_xch[i]>dt5:
                flow_xch.remove(i)
        items = []
        top10result = []
        if top10:
            p2t = {'91':[20,5],'90':[5,4],'0':[10,4],'1':[10,4],'2':[10,4]}
            
            for prefix in prefix_checktable:
                if prefix_checktable[prefix]:
                    top10result += get10Top(prefix,p2t[prefix][0],p2t[prefix][1])
        def top10filter(c):
            if top10:
                return c[1] in top10result
            else:
                return True
        bte = d[-1]-timedelta(days=1)
        RISE = searchRise(companys,k,d,ky,dy)
        for i in range(len(companys)):
            code = companys[i][1]
            if code in bos:
                isnew = False #和昨天比
                bolls = []
                periods = []
                if not stock.isStrongBollway(bos[code]):
                    continue
                for bo in bos[code]:
                    if bo[8]<bte: #通道结束不要超过1天
                        continue
                    #最近股价要大于通道顶，同时要大于通道里面的全部k线
                    #bo (0 timestramp,1 period,2 n,3 up,4 down,5 mink,6 maxk,7 tbi,8 tei,9 zfn)
                    if companys[i][3] in prefix_checktable and prefix_checktable[companys[i][3]] and bo[1] in peroid_checktable and peroid_checktable[bo[1]] and top10filter(companys[i]):
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
                if k.shape[1]>1 and k[i,-1,3]+k[i,-1,4]>0 and k[i,-2,3]+k[i,-2,4]<0 and (companys[i][3]=='90' or companys[i][3]=='91'):#查找那些主力先流出后流入的
                    flow_xch[i] = t
                if len(bolls)>0 and ((news==1 and isnew) or (news==0 and not isnew)) or news==2 or i in flow_xch:
                    ALLBOLLS.append((companys[i],bolls,i,k[i,-1,1]))
                    items.append((k[i,-1,1],i,companys[i][1],periods))
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
        ALLBOLLS = sorted(ALLBOLLS,key=lambda it:it[3],reverse=True if switch!=5 else False)
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
        sorteditems = sorted(items,key=lambda it:it[0],reverse=True if switch!=5 else False)
        button_items = []
        for it in sorteditems:
            if it[2] in FILTERCOLORS:
                i = it[1]
                periods = it[3]
                if k.shape[1]>1:
                    hugv = k[i,-1,3]+k[i,-1,4]
                    if hugv>0:
                        style = "#FF80FF" if hugv>k[i,-2,3]+k[i,-2,4] else "#FF8080"
                    elif hugv<0:
                        style = "#FFA500" if hugv>k[i,-2,3]+k[i,-2,4] else "#00A800"
                    else:
                        style = '#C8C8C8'
                else:
                    style = '#C8C8C8'                  
                if companys[i][1] in RISE:
                    style = '#FF00FF'
                    but = widgets.Button(
                        description="(%d) %s%%%s%s"%(RISE[companys[i][1]],k[i,-1,1],companys[i][2],str(periods)),
                        disabled=False,
                        icon='cannabis',
                        layout=Layout(width='240px'))
                else:
                    but = widgets.Button(
                        description="%s%%%s%s"%(k[i,-1,1],companys[i][2],str(periods)),
                        disabled=False,
                        icon='cannabis',
                        layout=Layout(width='240px'))           
                but.style.button_color = style
                but.event = ('bollup',companys[i],periods)
                but.bolls = bolls
                but.code = companys[i][1]
                but.on_click(onkline)                
                button_items.append(but)
        """
        box = Box(children=items[:32],layout=box_layout)
        fmt = InteractiveShell.instance().display_formatter.format
        data, metadata = fmt(box)
        list_output.outputs = ({
            'output_type': 'display_data',
            'data':data,
            'metadata': metadata
        },)
        """                
        #list_output.clear_output(wait=True)
        #with list_output:
        #    display(Box(children=items[:32],layout=box_layout))
        #list_output.append_display_data(Box(children=items[:32],layout=box_layout))
        update_current_plot(k,d)   
        update_top_plot(k,d)
        list_box.children = button_items
    """
    绘制一个大盘涨幅和资金流，行业前10的，概念前10的
    """
    def update_top_plot(k=None,d=None):
        nonlocal companys,code2i,kview_output
        
        if k is None:
            t = datetime.today()
            b,k,d = get_last_rt(t)
            if not b:
                return
        gs_kw = dict(width_ratios=[1,1], height_ratios=[2,1,2,1])
        fig,axs = plt.subplots(4,2,figsize=(18,16),gridspec_kw = gs_kw)
        
        SP = (np.argsort(k[:,-1,1]),np.argsort(k[:,-1,3]+k[:,-1,4])) #资金
        x = np.arange(k.shape[1])
        xticks = [0,60-15,2*60-15,3*60+15,4*60+15]
        for p in [('90',(0,0),(1,0),'行业涨幅前5',0),('91',(0,1),(1,1),'概念涨幅前5',0),('90',(2,0),(3,0),'行业资金前5',1),('91',(2,1),(3,1),'概念资金前5',1)]:
            tops = []
            sp = SP[p[4]]
            for i in range(len(sp)-1,0,-1):
                if companys[sp[i]][3] == p[0]:
                    tops.append(sp[i])
                    if len(tops)>4:
                        break
            for i in tops:
                axs[p[1]].set_title(p[3],y=0.93)
                axs[p[1]].plot(x,k[i,:,1],label=companys[i][2])
                axs[p[2]].plot(x,k[i,:,3]+k[i,:,4],label=companys[i][2])
                axs[p[2]].xaxis.set_major_formatter(MyFormatterRT(d,'h:m'))
                for j in (1,2):
                    axs[p[j]].axhline(y=0,color='black',linestyle='dotted')
                    axs[p[j]].set_xticks(xticks)
                    axs[p[j]].set_xlim(0,15+4*60)
                    axs[p[j]].grid(True,axis='x')
                axs[p[1]].legend()

        fig.subplots_adjust(hspace=0,wspace=0.08)
        kline.output_show(kview_output)
    """
    绘制更新选择的分时图表
    """
    def update_current_plot(k=None,d=None):
        nonlocal FILTERCURRENT,monitor_output,page,npage,pagedown,pageup,button_items
        if k is None:
            t = datetime.today()
            b,k,d = get_last_rt(t)
            if not b:
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
                if x==2 and y==3: #将上证放置在这个位置上
                    pass
                else:
                    views.append(c[0][1])
                    plotfs(ax,k[c[2],:,:],d,c[0][2],bolls=c[1])
        shi = code2i['SH000001']
        ax = [axs[2,3],axs[2+1,3]]
        plotfs(ax,k[shi,:,:],d,'上证指数')
        for but in button_items:
            if but.code in views:
                but.icon = 'check'
            else:
                but.icon = ''
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
    for it in [('5',5),('15',15),('30',30),('60',60)]:
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
    
    def on_top10check(e):
        nonlocal top10
        top10 = e['new']
        update_bollupbuttons()
    top10check = widgets.Checkbox(value=top10,description='top10过滤',disabled=False,layout=Layout(display='block',width='140px'))
    top10check.observe(on_top10check,names='value')
    checkitem.append(top10check)

    def on_refrush(e):
        nonlocal list_output,list_box,button_items
        list_output.clear_output(wait=True)
        list_box = Box(children=button_items,layout=box_layout)
        with list_output:
            display(list_box)
        update_current_plot()
    refrushbut = widgets.Button(
                description="刷新",
                disabled=False,
                button_style='')
    refrushbut.on_click(on_refrush)
    checkitem.append(refrushbut)

    def on_clear(e):
        kline_output.clear_output()
        kview_output.clear_output()
        update_current_plot()
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
        nonlocal page,npage,list_output,list_box,button_items
        page+=1
        if page>=npage:
            page = npage-1
        list_output.clear_output(wait=True)
        list_box = Box(children=button_items,layout=box_layout)
        with list_output:
            display(list_box)           
        update_current_plot()   
    pagedown = widgets.Button(
                description="下一页",
                disabled=False,
                button_style='')
    pagedown.on_click(on_pagedown)
    
    def on_pageup(e):
        nonlocal page,npage,list_output,list_box,button_items
        page-=1
        if page<0:
            page = 0
        list_output.clear_output(wait=True)
        list_box = Box(children=button_items,layout=box_layout)
        with list_output:
            display(list_box)            
        update_current_plot()
    pageup = widgets.Button(
                description="上一页",
                disabled=False,
                button_style='')
    pageup.on_click(on_pageup)
    checkitem.append(pageup)
    checkitem.append(pagedown)
    timeLabel = widgets.Label()
    checkitem.append(timeLabel)
    link1 = widgets.HTML(value="""<a href="http://vip.stock.finance.sina.com.cn/moneyflow/#sczjlx" target="_blank" rel="noopener">流向</a>""")
    link2 = widgets.HTML(value="""<a href="http://data.eastmoney.com/zjlx/dpzjlx.html" target="_blank" rel="noopener">资金</a>""")
    link3 = widgets.HTML(value="""<a href="http://summary.jrj.com.cn/dpyt/" target="_blank" rel="noopener">云图</a>""")
    checkitem+=[link1,link2,link3]
    checkbox = Box(children=checkitem,layout=box_layout)
    mbox = Box(children=[monitor_output,kview_output],layout=Layout(display='flex',flex_flow='row',align_items='stretch',min_width='3048px'))
    display(mbox,checkbox,list_output,kline_output)
    with list_output:
        display(list_box)

    lastminute = -1
    def loop():
        nonlocal timeLabel,lastminute
        t = datetime.today()
        timeLabel.value = '%d:%d:%d'%(t.hour,t.minute,t.second)
        if t.minute!=lastminute:
            lastminute = t.minute
            update_bollupbuttons()
        xueqiu.setTimeout(1,loop,'monitor.bollup')
    loop()    

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
个股和概念的匹配度排名列表
"""
def fits(code,day=3):
    R = stock.query("select code from emlist where emcode='%s'"%code)
    kdd = stock.query('select date from kd_xueqiu where id=8828 order by date desc limit %d'%day)
    bi = stock.dateString(kdd[-1][0])
    C,K,D = stock.loadKline(code,5,after=bi)
    P = (K[:,4]-K[0,4])/K[0,4]
    P = P/P.max()
    result = []
    for it in R:
        code = it[0]
        c,k,d = stock.loadKline(code,5,after=bi)
        if len(K)==len(k):
            p = (k[:,4]-k[0,4])/k[0,4]
            if p.max()>0:
                p = p/p.max()
                dp = p-P
                result.append((dp.sum(),np.abs(dp).sum(),code))
    return list(sorted(result,key=lambda it:it[1]))
  

"""
跟踪分类 90,概念 91,ETF 2
10:30点前，1 流入 2 放量 3 通道内突破5日线上
"""
def searchRise(companys,k,d,k2,d2,prefixs=('90','91','2')):
    K,D = xueqiu.get_period_k(15)
    bolls = bolltrench()
    R = []
    for i in range(len(companys)):
        if companys[i][3] in prefixs and i<k.shape[0] and i<k2.shape[0]:
            if k[i,-1,3]+k[i,-1,4]>0: #净流入
                ma5 = stock.ma(K[i,:],80)
                if k[i,-1,0]>=ma5[-1]: #大于5日均线
                    if True:#k[i,-1,2]>k2[i,k.shape[1]-1,2] and k[i,-1,1]>0: #放量上涨
                        if companys[i][1] in bolls:
                            R.append((companys[i],k[i,-1,1]))
    R = sorted(R,key=lambda it:it[1],reverse=True)
    result = {}
    count = {'90':0,'91':0,'2':0}

    for i in range(len(R)):
        if count[R[i][0][3]]<5:
            count[R[i][0][3]]+=1
            result[R[i][0][1]] = count[R[i][0][3]]
    return result
"""
分屏多窗口监控分时图
将每天上午10点涨幅排行放入监控列表
"""
def muti_monitor():
    monitor_output = widgets.Output()
    list_output = widgets.Output()
    companys = xueqiu.get_company_select()
    code2i = xueqiu.get_company_code2i()
    code2com = xueqiu.get_company_code2com()
    pages = Box(children=[])
    listbox = Box(children=[],layout=box_layout)
    prefix = '2'
    ntop = 3
    nday = 3
    npage = 0
    npos = 0
    curcode = ''
    curlist = []
    flashButs = []
    def update_plot(data,row=4,col=5,figsize=(50,20)):
        gs_kw = dict(height_ratios=[3,1,3,1])
        fig,axs = plt.subplots(row,col,figsize=figsize,gridspec_kw = gs_kw)
        for i in range(int(row*col/2)):
            if i<len(data):
                p = data[i]
                x = 2*int((i)/col)
                y = (i)%col
                ax = [axs[x,y],axs[x+1,y]]
                plotfs(ax,p[0],p[1],p[2],ma5b=p[3],topshow=(p[8],p[7]))
        fig.subplots_adjust(hspace=0,wspace=0.08)
        kline.output_show(monitor_output)
    def on_page(e):
        nonlocal pages,npage
        for but in pages.children:
            but.button_style = ''
        e.button_style='success'
        npage = int(e.description)
        update()
    def update_pages(N):
        nonlocal pages
        ps = []
        for i in range(N):
            ps.append(widgets.Button(description=str(i),button_style='success' if i==0 else ''))
            ps[-1].on_click(on_page)
        pages.children = ps
    def on_show(e):
        nonlocal list_output,curcode
        list_output.clear_output()
        with list_output:
            curcode = e.code
            K(e.code)
    def update():
        nonlocal companys,prefix,ntop,nday,npage,npos,curlist,flashButs
        t = date.today()
        eit = None
        if npos==0:
            lastt,k,d = get_last_rt(t)
            _,k2,d2 = get_last_rt(lastt-timedelta(days=1))
        else:
            lastt,k,d = get_last_rt(t-timedelta(days=math.floor(-npos/255)))
            _,k2,d2 = get_last_rt(lastt-timedelta(days=1))
            j = -((-npos)%255)-1
            k = k[:,:j,:]
            d = d[:j]
            eit = d[-1]
        RISE = searchRise(companys,k,d,k2,d2)
        if True:
            code2gl = {} #代码对应的概念
            if prefix=='MSCI':
                prefixs = []
                for r in (get10Top('90',5,3,eit), get10Top('91',10,3,eit)):
                    for c in r:
                        qs = stock.query("select code from emlist where emcode='%s'"%c)
                        for cc in qs:
                            if cc[0] in code2i:
                                if cc[0] in code2gl:
                                    code2gl[cc[0]].append(c)
                                else:
                                    code2gl[cc[0]] = [c]
                                prefixs.append(cc[0])
                R = get10Top(prefixs,ntop,nday,eit,detail=True)
            elif prefix=='FAV':
                today = date.today()  
                after = today-timedelta(days=nday)
                result = stock.query("select * from notebook where date>='%s' order by date desc"%(stock.dateString(after)))
                R = [('SH000001',None,0),('SZ399001',None,0)]            #将大盘加入其中
                T = {}
                for it in result:
                    if it[2] not in R and it[2] not in T:
                        T[it[2]] = 1
                        R.append((it[2],None,0))
            else:
                R = get10Top(prefix,ntop,nday,eit,detail=True)
                R2 = getCrossMa(prefix,[5,10,20,30])

            K,D = xueqiu.get_period_k(15)
            data = []
            bi = 0
            for i in range(-1,-len(D),-1):
                if eit is None or eit>=D[i][0]:
                    if D[i][0].hour==15:
                        bi = i
                        break
            for it in R:
                code = it[0]
                if code in code2i:
                    i = code2i[code]
                    if i<k2.shape[0] and i<k.shape[0]:
                        ma5 = stock.ma(K[i,:],80) #计算5日均线起点和终点
                        #将昨天的数据补在前面
                        glstr = ''
                        if companys[i][1] in code2gl:
                            for c in code2gl[companys[i][1]]:
                                glstr += ' %s'%code2com[c][2]
                        if len(d)>=254:
                            data.append((k[i,:,:],d,companys[i][2]+glstr,ma5[bi],i,(k[i,bi,0]-ma5[bi])/ma5[bi],code,it[1],it[2]))
                        else:
                            #这里要重新计算昨天的涨幅
                            tk = np.vstack((k2[i,-255+len(d):,:],k[i,:,:]))
                            openp = tk[-1,0]/(1.+tk[-1,1]/100.)
                            tk[:255-len(d),1] = 100*(tk[:255-len(d),0]-openp)/openp
                            data.append((tk,d2[-255+len(d):]+d,companys[i][2]+glstr,ma5[bi],i,(k[i,bi,0]-ma5[bi])/ma5[bi],code,it[1],it[2]))

            data = sorted(data,key=lambda it:it[5],reverse=True)
            curlist = []
            buts = []
            flashButs = []
            for j in range(len(data)):
                it = data[j]
                i = it[4]
                code = it[6]
                curlist.append(code)
                ii = code2i[code]
                if k.shape[1]>1:
                    hugv = k[ii,-1,3]+k[ii,-1,4]
                    if hugv>0:
                        style = "#FF80FF" if hugv>k[ii,-2,3]+k[ii,-2,4] else "#FF8080"
                    elif hugv<0:
                        style = "#FFA500" if hugv>k[ii,-2,3]+k[ii,-2,4] else "#00A500"
                    else:
                        style = '#C8C8C8'
                else:
                    style = '#C8C8C8'
                if companys[i][1] in RISE:
                    style = '#FF00FF'
                    buts.append(widgets.Button(description="(%d) %s%.1f%%"%(RISE[companys[i][1]],companys[i][2],100*it[5]),icon='check' if j>=10*npage and j<10*npage+10 else ''))
                    flashButs.append(buts[-1])
                else:
                    buts.append(widgets.Button(description="%s%.1f%%"%(companys[i][2],100*it[5]),icon='check' if j>=10*npage and j<10*npage+10 else ''))
                buts[-1].style.button_color = style
                buts[-1].code = companys[i][1]
                buts[-1].on_click(on_show)                
            listbox.children = buts
            update_plot(data[10*npage:])
            return data
        return []
    lastt = None
    def loop():
        nonlocal npos,lastt,flashButs
        t = datetime.today()
        if (lastt is None or (lastt is not None and t.minute!=lastt.munute)) and stock.isTransDay() and stock.isTransTime():
            npos = 0
            lastt = t
            update()
        elif stock.isTransTime():
            for but in flashButs:
                if but.style.button_color!='#FF00FF':
                    but.style.button_color = '#FF00FF'
                else:
                    but.style.button_color = '#C8C8C8'
        
        xueqiu.setTimeout(1,loop,'monitor.muti_monitor')
    tools = []
    def on_switch(e):
        nonlocal prefix,ntop,nday,npage
        prefix = e.prefix
        ntop = e.ntop
        nday = e.nday
        npage = 0
        for but in tools:
            if type(but)==Button and but.button_style=='success':
                but.button_style = ''
        e.button_style='success'
        data = update()
        update_pages(math.ceil(len(data)/10.))
    for it in (('概念','91',20,5),('行业','90',5,4),('ETF','2',8,4),('SH','1',10,4),('SZ','0',10,4),('叠加MSCI','MSCI',20,4),('关注','FAV',20,3)):
        tools.append(widgets.Button(description=it[0],button_style='success' if it[1]==prefix else ''))
        tools[-1].on_click(on_switch)
        tools[-1].prefix = it[1]
        tools[-1].ntop = it[2]
        tools[-1].nday = it[3]
    
    tools.append(pages)
    #如果不是交易时间可以review
    def on_review(e):
        nonlocal npos
        if e.description=='>':
            npos+=15
        elif e.description=='<':
            npos-=15
        elif e.description=='>>':
            npos+=255
        else:
            npos-=255
        if npos>0:
            npos = 0
        update()
    for it in ('<<','<','>','>>'):
        tools.append(widgets.Button(description=it))
        tools[-1].on_click(on_review)
    def on_list(e):
        nonlocal curlist,npage
        list_output.clear_output()
        with list_output:
            for i in range(10*npage,10*npage+10):
                if i<len(curlist):
                    c = curlist[i]
                    K(c)
    tools.append(widgets.Button(description='列表'))
    tools[-1].on_click(on_list)
    def on_fit(e):
        nonlocal curcode,list_output
        if len(curcode)>5:
            with list_output:
                for it in fits(curcode):
                    if it[0]>0:
                        K(it[2])
    tools.append(widgets.Button(description='匹配'))
    tools[-1].on_click(on_fit)    
    tool_box = Box(children=tools,layout=box_layout)
    update()
    loop() 
    display(monitor_output,tool_box,listbox,list_output)

"""
返回指定类型的 通道增幅/通道长度 ,这是数字越小排名越靠前
"""
def bolltops(prefix='91',ntops=10):
    c2c = xueqiu.get_company_code2com()
    _,k,d = get_last_rt(date.today())
    dt = timedelta(days=1)
    bolls = bolltrench()
    S = []
    for (code,bo) in bolls.items():
        if code in c2c and c2c[code][3]==prefix:
            R = 100
            RB = None
            for b in bo:
                rs = (b[6]-b[5])/b[5]
                if d[-1]-b[8]<dt and rs<0.04:
                    r = rs/b[2]
                    if r<R:
                        R = r
                        RB = b
            if R!=100:
                S.append((code,R,RB,c2c[code]))
    S = sorted(S,key=lambda it:it[1])
    return S[:ntops]

#早盘显示
"""
用于早盘追涨
review复盘
review = 日期，DT=多少秒更新一次
"""
def riseview(review=None,DT=60,BI=18):
    companys = xueqiu.get_company_select()
    code2i = xueqiu.get_company_code2i()
    kview_output = widgets.Output()
    toolbox = Box(children=[],layout=box_layout)
    kout = widgets.Output()
    last2daymin = None
    buts = []

    #通道长度基本不变在开始就准备好
    longboll = []
    for it in (('91',60),('2',10)):
        b = bolltops(it[0],ntops=it[1])
        for c in b:
            longboll.append(c[0])

    """
    净流入涨幅榜
    返回[(com,日涨幅,成交量增加率,流入),...]
    """
    def rise(k,d,k2,d2,prefixs=('91','2')):
        nonlocal companys
        K,D = xueqiu.get_period_k(15)
        if review is not None:
            for i in range(len(D)-1,0,-1):
                if D[i][0].day==d[-1].day and D[i][0].hour==d[-1].hour and D[i][0].minute>=d[-1].minute:
                    K = K[:,:i]
                    D = D[:i]
        
        R = []
        """
        结束
        """
        bolls = bolltrench()
        if d[-1].hour==9 and d[-1].minute<=30:
            for i in range(len(companys)):
                if companys[i][3] in prefixs and companys[i][1] in bolls and i<k.shape[0] and k[i,-1,1]>0:
                    R.append((companys[i],k[i,-1,1],k[i,-1,1],k[i,-1,1],stock.getBollwayRange(bolls[companys[i][1]]))) #company,涨幅,量增幅比率,流入
        else:
            for i in range(len(companys)):
                if companys[i][3] in prefixs and i<k.shape[0] and i<k2.shape[0]:
                    if k[i,-1,3]+k[i,-1,4]>0: #净流入
                        ma5 = stock.ma(K[i,:],80)
                        if k[i,-1,0]>=ma5[-1] and k[i,-1,1]>0: #大于5日均线并且要求增长
                            if companys[i][1] in bolls:
                                r = 0
                                if k.shape[1]-1<k2.shape[1] and k2[i,k.shape[1]-1,2]>0:
                                    r = k[i,-1,2]/k2[i,k.shape[1]-1,2]
                                rang = stock.getBollwayRange(bolls[companys[i][1]]) if stock.isStrongBollway(bolls[companys[i][1]]) else (0,0)
                                R.append((companys[i],k[i,-1,1],r,k[i,-1,3]+k[i,-1,4],rang)) #company,涨幅,量增幅比率,流入
                        else: #如果回到通道内给机会
                            if companys[i][1] in bolls:
                                r = 0
                                if k.shape[1]-1<k2.shape[1] and k2[i,k.shape[1]-1,2]>0:
                                    r = k[i,-1,2]/k2[i,k.shape[1]-1,2]
                                rang = stock.getBollwayRange(bolls[companys[i][1]]) if stock.isStrongBollway(bolls[companys[i][1]]) else (0,0)
                                if rang[0]>0 and k[i,-1,0]>rang[0]:
                                    R.append((companys[i],k[i,-1,1],r,k[i,-1,3]+k[i,-1,4],rang)) #company,涨幅,量增幅比率,流入

        return R
    """
    流入速率于涨幅速率榜
    """
    def riserate(k,d,k2,d2,prefixs=('91','2')):
        R = []
        if k.shape[1]>5:
            bolls = bolltrench()
            for i in range(len(companys)):
                if companys[i][3] in prefixs and i<k.shape[0]:
                    if k[i,-1,3]!=0 and k[i,-1,4]!=0:
                        F = k[i,:,3]+k[i,:,4]
                        F[F!=F]=0 #消除NaN
                        m0 = stock.ma(F,3)
                        m1 = stock.ma(F,30)
                        j = -1
                        for j in range(-1,-k.shape[1]+2,-1):
                            if m1[j]>m0[j]: #长期大于短期
                                break
                        if j!=-1:
                            dhug = (F[-1]-m1[j])
                            if dhug>=0:
                                R.append((companys[i],k[i,-1,1],dhug,0,(0,0)))#company,涨幅,涨幅增量+流入增量,0

        return R
    #0 company_id,1 code,2 name,3 prefix
    #0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting
    #返回 (code,涨幅/增长/流入,company)
    def getTops(R,prefix,sortcoln):
        S = []
        for r in R:
            if r[0][3]==prefix: 
                S.append((r[0][1],r[sortcoln],r[0],r[4]))
        S = sorted(S,key=lambda it:it[1],reverse=True)
        return S

    def on_show(e):
        nonlocal kout
        kout.clear_output()
        with kout:
            K(e.code)
    def on_shollall(e):
        nonlocal kout,buts,code2i,companys
        kout.clear_output()
        with kout:
            for but in buts:
                if but.code in code2i and companys[code2i[but.code]][3]==e.perfix:
                    K(but.code)
    #列出全部概念，或者全部ETF
    TOOLBUTS = []
    for it in (('列概念','91'),('列ETF','2')):
        TOOLBUTS.append(widgets.Button(description=it[0]))
        TOOLBUTS[-1].perfix = it[1]
        TOOLBUTS[-1].on_click(on_shollall)
    def on_clear(e):
        nonlocal kout
        kout.clear_output()
    TOOLBUTS.append(widgets.Button(description='清除'))
    TOOLBUTS[-1].on_click(on_clear)
    def update(offset=None):
        nonlocal code2i,companys,kview_output,toolbox,TOOLBUTS,buts
        if review is None:
            t = datetime.today()
        else:
            t = datetime.fromisoformat(review)
        lastt,k,d = get_last_rt(t)
        if offset is not None and offset<k.shape[1]:
            k = k[:,:offset,:]
            d = d[:offset]
        _,k2,d2 = get_last_rt(lastt-timedelta(days=1))   

        a = None

        if stock.isTransTime() and stock.isTransDay() and t.hour==9 and t.minute>=30: #一般数据更新周期1分钟，这里对最后的数据做即时更新
            b,a,ts,rtlist = xueqiu.getEmflowRT9355()
            if b:
                k = np.copy(k)
                for j in range(len(rtlist)):
                    c = rtlist[j][2]
                    i = code2i[c]
                    if i<k.shape[0]:
                        k[i,-1,:] = a[j,-1,:]

        R = rise(k,d,k2,d2)         #
        R2 = riserate(k,d,k2,d2)    #
        gs_kw = dict(width_ratios=[1,1], height_ratios=[2,1,2,1])
        fig,axs = plt.subplots(4,2,figsize=(48,20),gridspec_kw = gs_kw)
        if a is None:
            xticks = [0,60-15,2*60-15,3*60+15,4*60+15]
        else: #开始交易的15分钟使用5秒间隔个数据
            k = np.zeros((k.shape[0],a.shape[1],a.shape[2]))
            for i in range(a.shape[0]):
                c = rtlist[i][2]
                j = code2i[c]
                k[j,:,:] = a[i,:,:]
            d = ts
            xticks = [i for i in range(0,12*30,12)]
        x = np.arange(k.shape[1])

        #计算盘前开始于结束
        pbi = 0
        for i in range(len(d)-1,0,-1):
            if d[i].hour==9 and (d[i].minute==15 or d[i].minute==16):
                pbi=i
                break
        comps = []
        LS = [('91',(0,0),(1,0),'概念涨幅',10,1,True),('2',(2,0),(3,0),'ETF涨幅',10,1,True),('91',(0,1),(1,1),'概念即时',10,2,False),('2',(2,1),(3,1),'ETF即时',10,2,False)]
        TOPS = []
        CODES = []
        for i in range(len(LS)):
            p = LS[i]
            if p[6]:
                S = getTops(R,p[0],p[5])                
            else:
                S = getTops(R2,p[0],p[5])
            TOPS.append(S[:p[4]])
            CODES.append([])
            for it in TOPS[-1]:
                CODES[-1].append(it[0])
                
        def is2has(code,profix):
            if profix=='91':
                return code in CODES[0] and code in CODES[2]
            else:
                return code in CODES[1] and code in CODES[3]
        def smoothwidth(v,w=5): #如果v折返越小w越接近于5，否则越接近于1
            r = stock.smooth(v)-0.7
            r*=3.33
            if r<0:
                r = 0
            if r>1:
                r = 1
            return r*5+1*(1-r)
        for i in range(len(LS)):
            p = LS[i]
            tops = TOPS[i]

            for j in range(len(tops)):
                it = tops[j]
                i = code2i[it[0]]
                if it[2] not in comps:
                    comps.append((it[2],it[3]))
                axs[p[1]].set_title("%s %d-%d %d:%d"%(p[3],d[-1].month,d[-1].day,d[-1].hour,d[-1].minute),y=0.93)
                lw = 1
                label = companys[i][2]
                if is2has(it[0],p[0]): #同时存在于价格榜和流入涨幅榜
                    lw += 1
                    label = companys[i][2] #r"$\bf{%s}$"%(companys[i][2]) #汉字不能加粗？
                zpl = axs[p[1]].plot(x,k[i,:,1],label=label,linewidth=lw)
                #相对值
                hug = k[i,:,3]+k[i,:,4]
                """
                hug[hug!=hug] = 0
                vmax = np.abs(hug).max()
                if vmax==0:
                    vmax = 1
                hug = hug/vmax
                """
                axs[p[2]].plot(x,hug,label=label,linewidth=smoothwidth(hug)) #绝对值
                #it[3] 是通道突破位置
                #这里计算突破为涨幅yp
                openp = k[i,-1,0]/(1.+k[i,-1,1]/100.) #简单反推下开盘价格
                down,up = it[3]
                if down!=0 and up!=0:
                    down_r = 100*(down-openp)/openp
                    up_r = 100*(up-openp)/openp
                    axs[p[1]].vlines(k.shape[1]+2*j+1,down_r,up_r,color=zpl[0]._color,linewidth=2*zpl[0]._linewidth)
                    axs[p[1]].axhline(y=down_r,linestyle='dotted',color=zpl[0]._color,linewidth=zpl[0]._linewidth)
                    axs[p[1]].axhline(y=up_r,linestyle='dashed',color=zpl[0]._color,linewidth=zpl[0]._linewidth)
                #axs[p[2]].plot(x,k[i,:,3]+k[i,:,4],label=label,linewidth=lw,linestyle='--' if not it[3] else None) #绝对值
                axs[p[2]].xaxis.set_major_formatter(MyFormatterRT(d,'h:m'))
                for j in (1,2):
                    axs[p[j]].axhline(y=0,color='black',linestyle='dotted')
                    axs[p[j]].set_xticks(xticks)
                    axs[p[j]].set_xlim(0,xticks[-1])
                    axs[p[j]].grid(True,axis='x')

                axs[p[1]].legend()
            if a is None:
                for j in (1,2):
                    bottom,top = axs[p[j]].get_ylim()
                    axs[p[j]].broken_barh([(pbi,15)], (bottom,top-bottom),facecolor='blue',alpha=0.1)  

        buts = []
        for it in comps:
            com = it[0]
            ge005 = it[1]
            buts.append(widgets.Button(description="%s"%(com[2])))
            i = code2i[com[1]]
            if k.shape[1]>1:
                if k[i,-1,3]+k[i,-1,4]>k[i,-2,3]+k[i,-2,4]: #流入
                    if k[i,-1,0]>k[i,-2,0]: #涨
                        color = '#FF8080' #流入涨 红
                    else:
                        if ge005:
                            color = '#FFA0FF' #流入跌 紫 并且在增长率>5%
                        else:
                            color = '#FF80FF' #流入跌 紫
                else: #流出
                    if k[i,-1,0]>k[i,-2,0]: #涨
                        color = '#FFA500' #流出涨 黄
                    else:
                        color = '#00A500' #流出跌 绿         
            else:
                color = '#C8C8C8'
            buts[-1].style.button_color = color
            if com[1] in longboll:
                buts[-1].style.font_weight = 'bold'
            buts[-1].code = com[1]
            buts[-1].on_click(on_show)   
        toolbox.children = buts+TOOLBUTS
        fig.subplots_adjust(hspace=0,wspace=0.04)
        kline.output_show(kview_output)
    #update end
    first = True
    if review is None:
        dt = None
    else:
        dt = BI
    def loop():
        nonlocal first,dt,DT
        if review is not None or (stock.isTransDay() and stock.isTransTime()):
            if review is None:
                t = datetime.today()
                if t.hour==9 and t.minute>=29:
                    DT = 5
                else:
                    DT = 60
            update(dt)
        elif first:
            update(dt)
        if review is not None:
            dt+=1
        first = False
        xueqiu.setTimeout(DT,loop,'monitor.riseview')
    mbox = Box(children=[kview_output],layout=Layout(display='flex',flex_flow='row',align_items='stretch',min_width='3048px'))
    display(mbox,toolbox,kout)
    loop()

def plotfs2(ax,k,d,title,rang=None,ma5b=None,fv=0,dt=60,ma60b=None,style=defaultPlotfsStyle):
    """
    k = (时间,(0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting)) , d = 时间戳 rang = (通道顶，通道底)
    ma5b 起始位置5日均线 fv=0 显示大资金，1显示成交量,fx=True标记流入和涨落的相关性
    """
    ax[0].set_title(title,y=0.93,fontdict={'fontweight':'bold'})
    x = np.arange(len(d))
    xticks = []
    fmt = 'd h:m'
    if dt==60:
        for i in range(len(d)):
            if (d[i].hour==9 and d[i].minute==30) or (d[i].hour==13 and d[i].minute==0):
                xticks.append(i)
        ax[0].set_xlim(0,255*3)
        ax[1].set_xlim(0,255*3)
    elif dt==5:
        for i in range(len(d)):
            if d[i].minute%5==0:
                if len(xticks)==0:
                    xticks.append(i)
                elif i-xticks[-1]>12:
                    xticks.append(i)
        fmt = 'h:m'
        ax[0].set_xlim(0,12*30)
        ax[1].set_xlim(0,12*30)

    #ax[0].axhline(y=0,color='black',linestyle='dotted')
    ax[0].plot(x,k[:,0],color=style['pcolor'])
    if ma60b is None:
        m60 = stock.ma(k[:,0],60)
    else:
        m60 = np.zeros((len(k),))
        m60[0] = ma60b
        for i in range(1,len(k)):
            m60[i] = m60[i-1]+(k[i,0]-m60[i-1])/(60*12) #这是一个近似迭代

    ax[0].plot(x,m60,color=style['ma60color'],linestyle=style['ma60linestyle'])#分时均线
    ax[0].text(len(d)-1,k[-1,0],"%0.2f"%k[-1,1],linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='left',verticalalignment='center',color='red' if k[-1,1]>0 else 'darkgreen')
    todaybi = 0
    if dt==60:
        for i in range(len(d)-1,0,-1):
            if d[i].day!=d[-1].day:
                todaybi = i+1
                break
    maxi = np.argmax(k[todaybi:,0])+todaybi
    mini = np.argmin(k[todaybi:,0])+todaybi
    if mini!=len(d)-1:
        ax[0].text(mini,k[mini,0],"%0.2f"%k[mini,1],linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='center',verticalalignment='top',color='red' if k[mini,1]>0 else 'darkgreen')
    if maxi!=len(d)-1:
        ax[0].text(maxi,k[maxi,0],"%0.2f"%k[maxi,1],linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='center',verticalalignment='bottom',color='red' if k[maxi,1]>0 else 'darkgreen')
    
    if ma5b is not None and len(k)>0:
        ma5 = np.zeros((len(k),))
        ma5[0] = ma5b[0]
        k15b = ma5b[1]
        if dt==60:
            N = 240*5
            M = 15
        elif dt==5:
            N = 240*5*12
            M = 15*12
        for i in range(1,len(k)):
            ma5[i] = ma5[i-1]+(k[i,0]-k15b[int(i/M)])/(N) #这是一个近似迭代
        ax[0].plot(x,ma5,linewidth=2,color='magenta',linestyle='dashed')
    if len(ax)==2:
        ax[1].axhline(y=0,color='black',linestyle='dotted')
        if fv==0:
            ax[1].plot(x,k[:,3]+k[:,4],color=style['maincolor']) #主力
            ax[1].plot(x,k[:,6],color=style['tingcolor']) #散
        elif fv==1:
            v = np.zeros((k.shape[0],))
            v[1:] = k[1:,2]-k[:-1,2]
            v[v!=v]= 0
            v[v<0] = 0
            ax[1].bar(x,v) #成交量
        else: #混合图
            v = np.zeros((k.shape[0],))
            v[1:] = k[1:,2]-k[:-1,2]
            v[v!=v]= 0
            v[v<0] = 0
            smax = k[k[:,6]==k[:,6],6].max()
            vmax = v[v==v].max()
            r = smax/vmax
            ax[1].plot(x,v*r) #成交量            
            ax[1].plot(x,k[:,3]+k[:,4],color=style['maincolor']) #主力
            ax[1].plot(x,k[:,6],color=style['tingcolor']) #散

        #ax[1].set_xlim(0,x[-1])
        ax[1].set_xticks(xticks)
        ax[1].xaxis.set_major_formatter(MyFormatterRT(d,fmt))  
    else:
        ax[0].xaxis.set_major_formatter(MyFormatterRT(d,fmt))

    ax[0].set_xticks(xticks)
    #ax[0].set_xlim(0,x[-1])
    ax[0].grid(True)
    ax[1].grid(True)
    if rang is not None and rang[0]!=0 and rang[1]!=0:
        ax[0].axhline(y=rang[0],linewidth=2,linestyle='dashed',color='green')
        ax[0].axhline(y=rang[1],linewidth=2,linestyle='dashed',color='red')
        ax[0].text(2,rang[0],"%0.2f"%(100*(rang[1]-rang[0])/rang[0]),fontsize=12,fontweight='black')
class Frame:
    """
    """
    companys = xueqiu.get_company_select()
    code2i = xueqiu.get_company_code2i()
    code2com = xueqiu.get_company_code2com()
    _uuid = random.randint(0,1e5)

    def __init__(self):
        self._id = Frame._uuid
        Frame._uuid+=1
        self._acct=0
        self._interval = 60
        self._lastt = None
        self._dataSource  = None
        self._plot_output = widgets.Output()
        self._output = widgets.Output()
        self._toolbox = Box(children=[],layout=box_layout)
        self._stocklistbox = Box(children=[],layout=box_layout)
        self._outbox = Box(children=[self._output],layout=Layout(display='flex',flex_flow='row',align_items='stretch',min_width='3048px'))
        mbox = Box(children=[self._plot_output],layout=Layout(display='flex',flex_flow='row',align_items='stretch',min_width='3048px'))
        display(mbox,self._toolbox,self._stocklistbox,self._outbox)
        self._toolbox_widgets = []
    def showStock(self,ls):
        """
        显示股票列表,ls = [code,...]
        调用plotStock显示，并调用listStock将股票按钮放入到_stocklistbox
        """        
        self.plotStock(ls)
        self.listStock(ls)

    def plt_show(self):
        kline.output_show(self._plot_output)
    def subplots(self,row=1,col=1,plot=None,source=None,figsize=(48,20)):
        """
        将股票列表显示在图表里面
        """
        gs_kw = dict(width_ratios=[1]*col, height_ratios=[2 if i%2==0 else 1 for i in range(row*2)])
        fig,axs = plt.subplots(row*2,col,figsize=figsize,gridspec_kw = gs_kw)
        
        fig.subplots_adjust(hspace=0,wspace=0.04)
        for i in range(col):
            for j in range(row):
                ax = (axs[(2*j,i)],axs[(2*j+1,i)])
                plot(ax,i,j,source)
        self.plt_show()

    def stock2button(self,code):
        """
        创建一个股票按钮
        """
        return widgets.Button(description="%s"%Frame.code2com[code][2])

    def K(self,code,period=15,pos=None,mode='auto'):
        kline.Plote(code,period,config={'index':True},mode=mode).show(figsize=(48,20),pos=pos)
    
    def listStock(self,ls):
        """
        将股票列表转换为按钮
        """
        def on_click(e):
            self._output.clear_output()
            with self._output:
                self.K(e._code)
        buts = []
        for code in ls:
            buts.append(self.stock2button(code))
            buts[-1]._code = code
            buts[-1].on_click(on_click)
        self._stocklistbox.children = buts

    def search(self):
        pass

    def update(self,t,lastt):
        """
        t 当前时间，lastt 上一次更新时间，第一次为None        
        """

    def loop(self):
        t = datetime.today()
        if self._acct>self._interval or self._lastt is None:
            self._acct=0
            self.update(t,self._lastt)
        else:
            dt = t-self._lastt
            self._acct += dt.seconds+dt.microseconds/1e6
        self._lastt = t
        #print('loop',self._acct,self._interval)
        xueqiu.setTimeout(1,self.loop,'monitor.Frame_%d'%self._id)

    def setUpdateInterval(self,a):
        """
        设置更新间隔，单位秒
        """
        self._interval = a
        self._acct = 0

    def toolbox_clear(self):
        self._toolbox_widgets = []
    def toolbox_update(self):
        self._toolbox.children = self._toolbox_widgets

    def toolbuttonbyid(self,id):
        for but in self._toolbox_widgets:
            if but.data==id:
                return but
        return None
    def toolbox_button(self,desc,data=None,disabled=False,button_style='',icon='',layout=Layout(),on_click=None,group=None,selected=False):
        """
        如果on_click=None将触发类方法on_click(data)
        可以将多个按钮编为一组group，相同组的按钮别点击时被标记
        """
        but = widgets.Button(description=desc,disabled=disabled,button_style=button_style,icon=icon,layout=layout)
        but.data = data
        but.group = group
        if selected:
            but.button_style='success'
        def onclick(e):
            e.button_style = 'warning'
            if on_click is None:
                self.on_click(e.data)
            else:
                on_click(e.data)
            if e.group is not None:
                for b in self._toolbox_widgets:
                    if type(b)==widgets.Button and b.group==e.group:
                        b.button_style=''
                e.button_style='success'
            else:
                e.button_style=''
        but.on_click(onclick)
        self._toolbox_widgets.append(but)
        return but
    def toolbox_checkbox(self,desc,value=False,data=None,disabled=False,icon='',layout=Layout(),on_check=None):
        """
        事件处理函数on_check(data,check)
        """
        but = widgets.Checkbox(description=desc,value=value,disabled=disabled,icon=icon,layout=layout)
        but.data = data
        def oncheck(e):
            if on_check is None:
                self.on_check(e['owner'].data,e['new'])
            else:
                on_check(e['owner'].data,e['new'])
        but.observe(oncheck,names='value')
        self._toolbox_widgets.append(but)
        return but
    def toolbox_dropdown(self,desc,options=[],value=None,data=None,disabled=False,layout=Layout(),on_list=None):
        but = widgets.Dropdown(description=desc,options=options,value=value,disabled=disabled,layout=layout)
        but.data = data
        def onlist(e):
            if on_list is None:
                self.on_list(e['owner'].data,e['new'])
            else:
                on_list(e['owner'].data,e['new'])
        but.observe(onlist,names='value')
        self._toolbox_widgets.append(but)
        return but

class HotPlot(Frame):
    TOP = 18
    def __init__(self):
        super(HotPlot,self).__init__()
        self._code2data = {}
        self._page = 0
        self._flowin = False
        self._hasboll = False
        self._reverse = False
        self._options = {'涨幅榜':self.riseTop,'流入榜':self.riseFlow,'活跃':self.activeTop}
        self._sel = list(self._options)[0]
        self._dataMethods = self._options[self._sel]
        self._dropdown = self.toolbox_dropdown('方法',list(self._options),self._sel,1)
        for it in [('ETF','2',1,True),('概念','91',1,False),('行业','90',1,False),('SZ','0',1,False),('SH','1',1,False),('指数',6,1,False),('持有',7,1,False),('上一页',3,None,False),('下一页',4,None,False),('实时',5,None,False)]:
            self.toolbox_button(it[0],it[1],group=it[2],selected=it[3])
        self.toolbox_checkbox('净流入',self._flowin,1,layout=Layout(display='block',width='80px'))
        self.toolbox_checkbox('有通道',self._hasboll,2,layout=Layout(display='block',width='80px'))
        self.toolbox_checkbox('反排序',self._reverse,3,layout=Layout(display='block',width='80px'))
        self.toolbox_update()
        self._prefix = ('2',)
        self._rt = 0 #0 普通60秒 1 5秒级别
        self._index = 0 #0 正常 1 显示指数 2 持有
        self._szk = None
    def on_click(self,data):
        if type(data)==str:
            self._page = 0
            self._prefix = (data,)
            self._index = 0
        if data==3: #pageup
            self._page-=1
        elif data==4: #pagedown
            self._page+=1
        elif data==5: #实时
            self._rt=1 if self._rt==0 else 0
            if self._rt==1:
                self.setUpdateInterval(5)
            else:
                self.setUpdateInterval(60)
        elif data==6: #指数
            self._index = 1 #
        elif data==7:
            self._index = 2 #持有
        self._output.clear_output()
        self.update(datetime.today(),None)
    def on_check(self,data,check):
        if data==1:
            self._flowin = check
        elif data==2:
            self._hasboll = check
        elif data==3:
            self._reverse = check
        self.update(datetime.today(),None)
    def on_list(self,data,sel):
        if data==1:
            self._sel = sel
            self._dataMethods = self._options[self._sel]
        self.update(datetime.today(),None)
    def stock2button(self,code):
        but = super(HotPlot,self).stock2button(code)
        data = self.code2data(code)
        if data is not None:
            k = data[2]
            if k.shape[0]>1:
                if k[-1,3]+k[-1,4]>k[-2,3]+k[-2,4]: #流入
                    if k[-1,0]>k[-2,0]: #涨
                        color = '#FF8080' #流入涨 红
                    else:
                        color = '#FF80FF' #流入跌 紫
                else: #流出
                    if k[-1,0]>k[-2,0]: #涨
                        color = '#FFA500' #流出涨 橙
                    else:
                        color = '#00A500' #流出跌 绿         
            else:
                color = '#C8C8C8'            
            but.style.button_color = color
            but.description = "%s %.2f%%"%(Frame.code2com[code][2],k[-1,1])
        return but

    def code2data(self,code):
        return self._code2data[code] if code in self._code2data else None

    def currentPageDataSource(self,dataSource,N):
        """
        数据在显示前进行前置处理
        1 受到翻页的影响 2 切换到5秒级别的数据
        """
        if self._page<0:
            self._page = 0
        if self._page>=math.ceil(len(dataSource)/N):
            self._page = math.ceil(len(dataSource)/N)-1
        viewdata = dataSource[self._page*N:]
        #viewdata ((0 company,1 涨幅(排序项) 2 k 3 d 4 K15 5 D15 6 bolls),...)
        for it in viewdata: #处理数据问题：1 价格为0
            k = it[2]
            for i in range(1,len(k)):
                if k[i,0]==0:
                    k[i,0] = k[i-1,0]
        R = []
        self._szk = None
        if self._rt==1 and len(viewdata)>0: #使用5秒级别的数据
            print('getEmflowRT9355',viewdata[0][3][-1])
            b,a,ts,rtlist = xueqiu.getEmflowRT9355(viewdata[0][3][-1])
            if b:
                c2i = {}
                for i in range(len(rtlist)):
                    c2i[rtlist[i][2]] = i
                    if rtlist[i][2]=='SZ399001':
                        self._szk = a[i]
                for it in viewdata:
                    if it[0][1] in c2i:
                        j = c2i[it[0][1]]
                        company = it[0]
                        bolls = it[6]
                        k = it[2]
                        d = it[3]
                        for i in range(len(d)-1,0,-1):
                            if d[i].day!=d[-1].day:
                                i+=1
                                break
                        ma60b = None
                        if i-60>0:
                            ma60b = k[i-60:i,0].sum()/60

                        rang = self.getStrongBollwaryRang(company[1],bolls)
                        R.append({'company':it[0],'k':a[j,:,:],'d':ts[:],'rang':rang,'ma5b':self.getma5b(it[4],it[5],0),'ma60b':ma60b,'dt':5})
                    else:
                        company = it[0]
                        rang = self.getStrongBollwaryRang(company[1],it[6])
                        R.append({'company':company,'k':it[2],'d':it[3],'rang':rang,'ma5b':self.getma5b(it[4],it[5]),'ma60b':None,'dt':60})
        else: #1分钟级别数据
            for it in viewdata: #处理ma5b,和rang
                company = it[0]
                rang = self.getStrongBollwaryRang(company[1],it[6])
                R.append({'company':company,'k':it[2],'d':it[3],'rang':rang,'ma5b':self.getma5b(it[4],it[5]),'ma60b':None,'dt':60})
        return R
    def getma5b(self,K15,D15,n=3):
        #f返回一个plotfs2 的ma5b需要的参数，用于绘制5日均线 n = 3起点位置在3天前
        if n==0:
            ma5b = K15[-16*n-16*5:].sum()/80
        else:
            ma5b = K15[-16*n-16*5:-16*n].sum()/80
        k15b = K15[-16*n-16*5:]
        return (ma5b,k15b)
    def update(self,t,lastt):
        if lastt is None or (stock.isTransDay() and stock.isTransTime()):
            if lastt is not None and t.hour==9 and t.minute==29:
                self._rt = 1
                self.setUpdateInterval(5)
                #print('setUpdateInterval',5)
            if self._index==1:
                self._dataSource = self.mapCode2DataSource(['SH000001','SZ399001','SZ399006','SH000688'])
            elif self._index==2:
                self._dataSource = self.mapCode2DataSource(stock.getHoldStocks())
            else:
                self._dataSource = self._dataMethods()
            self._code2data = {}
            for data in self._dataSource:
                self._code2data[data[0][1]] = data
            #print('update',t,lastt)
            self.subplots(2,3,self.riseTopPlot,source=self.currentPageDataSource(self._dataSource,2*3))
            self.listStock([it[0][1] for it in self._dataSource])

    def riseTopPlot(self,ax,i,j,source):
        n = i+3*j
        if n<len(source):
            s = source[n]
            company = s['company']
            k = s['k']
            d = s['d']
            rang = s['rang']
            ma5b = s['ma5b']
            ma60b = s['ma60b']
            dt =  s['dt']
            title = "%s %s"%(company[2],stock.timeString2(d[-1]))
            if self._szk is not None and self._index!=1 and self._szk.shape[0]==k.shape[0]: #将指数显示上去
                x = np.arange(len(d))
                kmax = k[:,0].max()
                kmin = k[:,0].min()
                szkmax = self._szk[:,0].max()
                szkmin = self._szk[:,0].min()
                if szkmax-szkmin!=0:
                    ax[0].plot(x,(self._szk[:,0]-szkmin)*(kmax-kmin)/(szkmax-szkmin)+kmin,color='black',alpha=0.4)
            plotfs2(ax,k,d,title,rang,ma5b,fv=3,dt=dt,ma60b=ma60b)
    def getCurrentRT(self):
        """
        返回当前数据
        """
        t = datetime.today()
        k,d = get_rt(4) #取得最近3天的1分钟数据(0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting)
        bi = -255*3
        k = k[:,bi:,:]
        d = d[bi:]
        k15,d15 = xueqiu.get_period_k(15)
        bolls = bolltrench()
        return k,d,k15,d15,bolls
    def isSelected(self,company,bolls,k):
        def onif(b,s):
            return (b and s) or not b
        return company[3] in self._prefix and onif(self._flowin,k[-1,3]+k[-1,4]>0) and onif(self._hasboll,company[1] in bolls)
    def riseTop(self,top=18):
        """
        涨幅排行,满足大资金流入，5日均线上有强通道或者返回强通道中
        返回值 [(com,price,hug,rang,k,d,ma5b),...]
        """
        k,d,K,D,bolls = self.getCurrentRT()
        companys = HotPlot.companys
        R = []
        for i in range(len(companys)):
            if i<k.shape[0] and self.isSelected(companys[i],bolls,k[i]):
                R.append((companys[i],k[i,-1,1],k[i],d,K[i],D,bolls)) #0 company,1 涨幅(排序项) 2 k 3 d 4 K15 5 D15 6 bolls
        TOPS = sorted(R,key=lambda it:it[1],reverse=not self._reverse)
        #将三点指数追加在末尾
        return TOPS[:top]
    def getStrongBollwaryRang(self,code,bolls):
        return stock.getBollwayRange(bolls[code]) if code in bolls else (0,0)
    def riseFlow(self,top=18):
        """
        流入排行榜
        """ 
        k,d,K,D,bolls = self.getCurrentRT()
        companys = HotPlot.companys   
        R = []
        if k.shape[1]>5:
            for i in range(len(companys)):
                if i<k.shape[0] and self.isSelected(companys[i],bolls,k[i]):
                    if k[i,-1,3]!=0 and k[i,-1,4]!=0:
                        F = k[i,:,3]+k[i,:,4]
                        F[F!=F]=0 #消除NaN
                        m0 = stock.ma(F,3)
                        m1 = stock.ma(F,30)
                        j = -1
                        for j in range(-1,-k.shape[1]+2,-1):
                            if m1[j]>m0[j]: #长期大于短期
                                break
                        if j!=-1:
                            dhug = (F[-1]-m1[j])
                            if dhug>=0:                              
                                R.append((companys[i],dhug,k[i],d,K[i],D,bolls))
        TOPS = sorted(R,key=lambda it:it[1],reverse=not self._reverse)
        #将三点指数追加在末尾
        return TOPS[:top]
    def activeTop(self,top=18):
        """
        最近比较活跃的
        """
        tb = {'90':(5,3),"91":(20,4),"2":(5,3),"0":(10,3),"1":(10,3)}
        it = tb[self._prefix[0]]
        TOPS = get10Top(self._prefix[0],it[0],it[1],reverse=not self._reverse)
        return self.mapCode2DataSource(TOPS)
    def mapCode2DataSource(self,codes,top=18):
        """
        将代码列表映射为数据源
        """
        k,d,K,D,bolls = self.getCurrentRT()
        companys = HotPlot.companys   
        R = []
        for code in codes:
            i = HotPlot.code2i[code]
            R.append((companys[i],k[i,-1,1],k[i],d,K[i],D,bolls))
        return R[:top]