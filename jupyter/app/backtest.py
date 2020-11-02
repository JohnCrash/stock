"""
使用5分钟数据对以下想法进行回测
在历史新高中选择股票做60分钟的macd周期,和固定板块中选择股票做60分钟的macd周期进行比较
将符合条件的股票对应的macd周期当成一个交易样本。计算全部这些样本然后数据进行分析。
"""
import numpy as np
from IPython.display import display,Markdown
from matplotlib.ticker import Formatter
import ipywidgets as widgets
from ipywidgets import Layout, Button, Box
import matplotlib.pyplot as plt
from datetime import date,datetime,timedelta
from . import shared
from . import stock
from . import xueqiu
from . import kline
from . import status
from . import mylog

"""
开始计算前先加载全部数据
k数据是一个矩阵竖向是company_select,横向是时间
v是成交量矩阵
d是时间戳
"""
def loadk_matrix(period=5,bi=None,progress=None,reload=False):
    if reload:
        shared.delKey('kmatrix_%d'%period)
        shared.delKey('vmatrix_%d'%period)
        shared.delKey('dvector_%d'%period)
    b,k5 = shared.numpyFromRedis('kmatrix_%d'%period)
    b2,v5 = shared.numpyFromRedis('vmatrix_%d'%period)
    b3,d5 = shared.fromRedis('dvector_%d'%period)    
    if b and b2 and b3:
        return k5,v5,d5
    company = xueqiu.get_company_select()
    if bi is None: #从2019-11-19日开始
        bi = '2019-11-19'
    #使用大盘确定时间戳数量
    if period==5:
        qk = stock.query("select timestamp,volume close from k5_xueqiu where id=8828 and timestamp>'%s'"%bi)
    else:
        qk = stock.query("select date,volume close from kd_xueqiu where id=8828 and date>'%s'"%bi)
    k5 = np.zeros((len(company),len(qk)))
    v5 = np.zeros((len(company),len(qk)))
    d5 = []
    for v in qk:
        d5.append((v[0],))
    if progress is not None:
        progress(0)
    for i in range(len(company)):
        if period==5:
            qk = stock.query("select timestamp,volume,close from k5_xueqiu where id=%d and timestamp>'%s'"%(company[i][0],bi))
        else:
            qk = stock.query("select date,volume,close from kd_xueqiu where id=%d and date>'%s'"%(company[i][0],bi))
        d = []
        k = np.zeros(len(qk))
        v = np.zeros(len(qk))
        for j in range(len(qk)):
            d.append((qk[j][0],))
            k[j] = qk[j][2]
            v[j] = qk[j][1]
        k = stock.alignK(d5,k,d)
        v = stock.alignK(d5,v,d)
        k5[i,:] = k
        v5[i,:] = v
        if i%100==0 and progress is not None:
            progress(i/len(company))
    xueqiu.nozero_plane(k5)
    xueqiu.nozero_plane(v5)
    if progress is not None:
        progress(1)
    shared.numpyToRedis(k5,'kmatrix_%d'%period,ex=24*3600) #保持一天
    shared.numpyToRedis(v5,'vmatrix_%d'%period,ex=24*3600)
    shared.toRedis(d5,'dvector_%d'%period,ex=24*3600)
    return k5,v5,d5

"""
返回从bi开始最高的价格
"""
def loadmax(bi=None,ei=None,progress=None,reload=False):
    if reload:
        shared.delKey('mmatrix_d')
    b,m = shared.numpyFromRedis('mmatrix_d')
    if b:
        return m
    if progress is not None:
        progress(0)        
    company = xueqiu.get_company_select()
    if bi is None:
        bi = '2003-01-01'
    if ei is None:
        ei = '2019-11-19'
    m = np.zeros(len(company))
    for i in range(len(company)):
        k = stock.query("select max(close) from kd_xueqiu where id=%d and date>'%s' and date<'%s'"%(company[i][0],bi,ei))
        m[i] = k[0][0]
        if i%100==0 and progress is not None:
            progress(i/len(company))        
    shared.numpyToRedis(m,'mmatrix_d',ex=24*3600)
    if progress is not None:
        progress(1)    
    return m

"""
检查loadk_matrix的日期是不是完整的时序，并且从9:35开始
"""
def checkPeriod5(d):
    if d[0][0].hour==9 and d[0][0].minute==35 and d[-1][0].hour==15 and d[-1][0].minute==0:
        for i in range(int(len(d)/48)):
            if d[i*48][0].hour==9 and d[i*48][0].minute ==35:
                continue
            else:
                print("发现",d[i*48],"不为9:35")
                return
        if len(d)%48!=0:
            print("时间长度不是48的整数倍",len(d),len(d)/48)
            for i in range(-1,-49,-1):
                print(d[i][0])
        else:
            #这里做严格的时序检查
            for i in range(1,len(d)):
                if (d[i][0]-d[i-1][0]).seconds==5*60:
                    continue
                elif d[i][0].day != d[i-1][0].day and d[i-1][0].hour==15 and d[i][0].hour==9 and d[i][0].minute==35:
                    continue
                elif d[i-1][0].hour==11 and d[i-1][0].minute==30 and d[i][0].hour==13 and d[i][0].minute==5:
                    continue
                else:
                    print("发现时序问题:",d[i-1][0],d[i][0])
            print("时序没有问题")
    else:
        print("开始时间和结束时间不是完整周期",d[0],d[-1])

def progress(i):
    print(i)


"""
将d5转换为d15,d30,...
"""
def periodD5(d,period):
    D = []
    n = period/5
    N = len(d)/n
    for i in range(1,int(N)):
        D.append(d[int(i*n)-1])
    return D
"""
从k5,d5转换为指定的时序,如period=60
"""
def periodBy5(k,v,d,period):
    if period==5:
        return k,d
    D = []
    ind = []
    n = period/5
    N = len(d)/n
    for i in range(1,int(N)):
        D.append(d[int(i*n)-1])
        ind.append(int(i*n)-1)
    return k[:,ind],D
"""
生产一个新高矩阵
"""
def newhigh(k,maxbi):
    n = np.zeros(k.shape)
    for i in range(k.shape[1]):
        if i==0:
            n[:,i] = maxbi
        else:
            n[:,i] = n[:,i-1]

        newhisel = k[:,i]>n[:,i]
        n[newhisel,i] = k[newhisel,i]
    return n
"""
准备数据需要的数据
rd
{
    periods:[5,15,30,60,120,...],#需要的时序
    macd:True ,#需要macd数据
    ma:[5,10,...] #均线
    boll:True ,#需要boll数据
    rsi:True  ,
    kdj:True  ,
}
"""
def init_context(rd):
    k5,v5,d5 = loadk_matrix()
    maxbi = loadmax()
    context = rd
    if 'periods' in rd:
        has5 = False
        for period in rd['periods']:
            if period==5:
                has5 = True
                break
        if not has5:
            rd['periods'].append(5)
        for period in rd['periods']:
            k,d = periodBy5(k5,v5,d5,period)
            context['k%d'%period] = k
            context['d%d'%period] = d
            #context['n%d'%period] = newhigh(k,maxbi) #新高
            if 'macd' in rd and rd['macd']:
                context['macd%d'%period],_,_ = stock.macdMatrix(k)
            if 'ma' in rd:
                ma = []
                for m in rd['ma']:
                    ma.append(stock.maMatrix(k,m))
                context['ma%d'%period] = ma
    timestamp2i = {}
    for i in range(len(d5)):
        timestamp2i[d5[i][0]] = i
    context["timestamp2i"] = timestamp2i
    return context

"""
将买卖点组合成交易对，并计算每次交易的收益率
"""
def combinTrans(context,buy,sell):
    result = []
    k5 = context['k5']
    timestamp2i = context['timestamp2i']
    for i in range(len(buy)):
        r = []
        buys = buy[i]
        sells = sell[i]
        for b in buys:
            r.append((True,b))
        for s in sells:
            r.append((False,s))
        r = sorted(r,key=lambda it:it[1][0])
        R = []
        b = None
        for o in r:
            if o[0] and b is None: #buy
                b = o[1]
            elif not o[0] and b is not None: #sell
                s = o[1]
                bi = timestamp2i[b[0]]
                si = timestamp2i[s[0]]
                R.append((b[0],s[0],bi,si,k5[i,si]/k5[i,bi]))
                b = None
        result.append(R)
    context['result'] = result
    return context

def macdGoldBuy(context):
    period = context['args']
    m = context['macd%d'%period]
    d = context['d%d'%period]
    result = []
    for i in range(m.shape[0]):
        r = []
        for j in range(1,m.shape[1]):
            if m[i,j-1]<0 and m[i,j]>0:
                r.append(d[j])
        result.append(r)
    return result

def macdDeathSell(context):
    period = context['args']
    m = context['macd%d'%period]
    d = context['d%d'%period]
    result = []
    for i in range(m.shape[0]):
        r = []
        for j in range(1,m.shape[1]):
            if m[i,j-1]>0 and m[i,j]<0:
                r.append(d[j])
        result.append(r)
    return result

def maBuy(context):
    period = context['args']
    ma = context['ma%d'%period]
    d = context['d%d'%period]
    result = []
    for i in range(ma[0].shape[0]):
        r = []
        for j in range(1,ma[0].shape[1]):
            if ma[0][i,j] > ma[1][i,j]:
                r.append(d[j])
        result.append(r)
    return result

def maSell(context):
    period = context['args']
    ma = context['ma%d'%period]
    d = context['d%d'%period]
    result = []
    for i in range(ma[0].shape[0]):
        r = []
        for j in range(1,ma[0].shape[1]):
            if ma[0][i,j] < ma[1][i,j]:
                r.append(d[j])
        result.append(r)
    return result

def backtest(rd,buy,sell):
    context = init_context(rd)
    return combinTrans(context,buy(context),sell(context))

"""
收益率在时序上的分布
"""
def period_distributed(period,context):
    N = period/5
    D = periodD5(context['d5'],period)
    result = context['result']
    x = np.arange(len(D))
    y = np.ones(len(D))
    n = np.zeros(len(D))
    for i in range(len(result)):
        ts = result[i]
        for t in ts:
            j = int(t[3]/N)-1
            y[j] += t[4]
            n[j] += 1
    s = n>0
    y[s] = y[s]/n[s]
    return x,y,D
"""
将结果绘制在时间周期上
"""
def backtestplot(context,period):
    periodDropdown = widgets.Dropdown(
        options=['日','120分钟','60分钟'],
        value='60分钟',
        description='周期',
        layout=Layout(display='block',width='120px'),
        disabled=False)
    box = Box(children=[periodDropdown],layout=status.box_layout)
    output = widgets.Output()
    display(box,output)

    def period_show(period):
        output.clear_output()
        x,y,D = period_distributed(period,context)
        fig,axs = plt.subplots(1,1,figsize=(32,14))
        axs.xaxis.set_major_formatter(status.MyFormatterRT(D,'m-d h:m'))
        xticks=[]
        N = int(len(D)/50)
        for i in range(len(D)):
            if i%N==0:
                xticks.append(i)
        with output:
            plt.plot(x,y)
            axs.grid(True)
            axs.set_xlim(0,len(D)-1)
            axs.set_xticks(xticks)                    
            fig.autofmt_xdate()
        kline.output_show(output)
    def on_period(e):
        name = e['new']
        if name=='日':
            period = 240
        elif name=='120分钟':
            period = 120
        else:
            period =60
        period_show(period)
    periodDropdown.observe(on_period,names='value')     

    period_show(period)
"""
使用弱周期跌幅和强周期涨幅来排名加仓
"""
def test():
    pass
