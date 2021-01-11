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
period 可以等于5或者'd'
bi 矩阵加载开始时间
ex 矩阵加载缓存保存时间
volume 是不是加载成交量矩阵
返回:
k数据是一个矩阵竖向是company_select,横向是时间
v是成交量矩阵
d是时间戳
"""
def loadk_matrix(period=5,bi=None,progress=None,reload=False,ex=24*3600,volume=False):
    if reload:
        shared.delKey('kmatrix_%s'%period)
        shared.delKey('vmatrix_%s'%period)
        shared.delKey('dvector_%s'%period)
    b,k5 = shared.numpyFromRedis('kmatrix_%s'%period)
    b2,v5 = shared.numpyFromRedis('vmatrix_%s'%period)
    b3,d5 = shared.fromRedis('dvector_%s'%period)
    if volume: 
        if b and b2 and b3:
            return k5,v5,d5
    else:
        if b and b3:
            return k5,None,d5
    company = xueqiu.get_company_select()
    if bi is None: #从2019-11-19日开始
        if period==5:
            bi = '2019-11-19'
        else:
            bi = '2012-01-01'
    #使用大盘确定时间戳数量
    if period==5:
        qk = stock.query("select timestamp,volume close from k5_xueqiu where id=8828 and timestamp>'%s'"%bi)
    else:
        qk = stock.query("select date,volume close from kd_xueqiu where id=8828 and date>'%s'"%bi)
    k5 = np.zeros((len(company),len(qk)))
    if volume:
        v5 = np.zeros((len(company),len(qk)))
    else:
        v5 = None
    d5 = []
    for v in qk:
        d5.append((v[0],))
    if progress is not None:
        progress(0)
    if volume:
        qs = "volume,close"
    else:
        qs = "close"
    for i in range(len(company)):
        if period==5:
            qk = stock.query("select timestamp,%s from k5_xueqiu where id=%d and timestamp>'%s'"%(qs,company[i][0],bi))
        else:
            qk = stock.query("select date,%s from kd_xueqiu where id=%d and date>'%s'"%(qs,company[i][0],bi))
        d = []
        k = np.zeros(len(qk))
        if volume:
            v = np.zeros(len(qk))
            for j in range(len(qk)):
                d.append((qk[j][0],))
                k[j] = qk[j][2]
                v[j] = qk[j][1]
            v = stock.alignK(d5,v,d)
            v5[i,:] = v
        else:
            for j in range(len(qk)):
                d.append((qk[j][0],))
                k[j] = qk[j][1]
        k = stock.alignK(d5,k,d)
        k5[i,:] = k
        if i%10==0 and progress is not None:
            progress(i/len(company))
    xueqiu.nozero_plane(k5)
    if volume:
        xueqiu.nozero_plane(v5)
    if progress is not None:
        progress(1)
    shared.numpyToRedis(k5,'kmatrix_%s'%period,ex=ex) #保持一天
    if volume:
        shared.numpyToRedis(v5,'vmatrix_%s'%period,ex=ex)
    shared.toRedis(d5,'dvector_%s'%period,ex=ex)
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
检查loadk_matrix的5分钟日期是不是完整的时序，并且从9:35开始
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
                #(0买入点时间，1卖出点时间，2买入点时间索引，3卖出点时间索引，4收益率)
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

"""
对macd的买入优化
"""
def macdGoldBuy2(context):
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

"""
对macd的卖出优化
"""
def macdDeathSell2(context):
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

"""
选一个macd时序
根据前两个的macd的最低点不创出新低，最近的macd<0在以前的低点附近出现连续的k线向上或者macd>0
本次
"""
def qsBuy(context):
    return result
"""
突破boll顶部后连续两根实体在顶部之下,macd<0减仓
"""
def qsBuy(context):
    pass

"""
顺大势逆小势
"""
def snBuy(context):
    return result
"""
顺大势逆小势
"""
def snBuy(context):
    pass

"""
zs2buy
*1.5分钟的ma240的斜率水平时,在60分钟布林底线附近买入
3.5分钟的ma240的斜率向上时,在ma240和ma60乖离率最低点买入，买入点不破ma240下方
"""
def zs2Buy(context):
    pass
"""
zs2Sell
*1.5分钟的ma240的斜率水平时，在60分钟布林通道顶附近卖出
2.5分钟的ma240的斜率向上时，在ma240和ma60乖离率最大点卖出
3.5分钟的ma240的斜率向下时，在ma240和ma60乖离率最低卖出
"""
def zs2Buy(context):
    pass

def backtest(rd,buy,sell):
    context = init_context(rd)
    return combinTrans(context,buy(context),sell(context))

"""
全部平均收益率在时序上的分布
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
将此方法的市场平均收益率绘制在时间周期上
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