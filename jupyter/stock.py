import MySQLdb
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import math
import ipywidgets as widgets
from IPython.display import display
from ipywidgets import Layout, Button, Box

"""
加载股票数据
返回的第一个数据
company{
    0 - id,
    1 - code,
    2 - name,
    3 - category,
    4 - done,
    5 - kbegin,
    6 - kend
    ...
}
kline {
    0 - volume,
    1 - open,
    2 - high,
    3 - low,
    4 - close,
    5 - macd
}
kdate {
    0 - [date,]
}
"""
def loadKline(code):
    db = MySQLdb.connect("localhost", "root", "789", "stock", charset='utf8',port=3307 )
    db.query("""select * from company where code='%s'"""%code)
    r = db.store_result()
    company = r.fetch_row()
    db.query("""select volume,open,high,low,close,macd from kd_xueqiu where id=%s"""%company[0][0])
    r = db.store_result()
    k = r.fetch_row(r.num_rows())
    db.query("""select date from kd_xueqiu where id=%s"""%company[0][0])
    r = db.store_result()
    kdate = r.fetch_row(r.num_rows())
    db.close()
    kline = np.array(k).reshape(-1,6)
    return company,kline,kdate

"""计算指数移动平均线ema,公式来源于baidu"""
def ema(k,n):
    m = np.empty([len(k)])
    for i in range(len(k)):
        if i==0:
            m[0] = k[i,4]
        else:
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
    emA = np.empty([len(k),3])
    emA[:,0] = ema9
    emA[:,1] = ema12
    emA[:,2] = ema26
    return 224.*ema9/51.-16.*ema12/3.+16.*ema26/17.,emA

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
        
"""计算kdj
n日RSV=（Cn－Ln）/（Hn－Ln）×100
公式中，Cn为第n日收盘价；Ln为n日内的最低价；Hn为n日内的最高价。
"""
def kdj(k,n):
    kdj = np.empty([len(k),3]) #K,D,J
    for i in range(len(k)):
        if i-n+1>=0:
            prevn = k[i-n+1:i+1,2:4]
        else:
            prevn = k[0:i+1,2:4]
        Ln = prevn.min()
        Hn = prevn.max()
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
    for i in range(len(k)):
        if i-n+1>=0:
            m[i] = k[i-n+1:i+1,4].sum()/n
        else:
            m[i] = k[0:i+1,4].sum()/(i+1)
    return m

"""计算指定范围的均线值"""
def maRange(k,n,bi,ei):
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
def SlopeRates(m):
    r = np.empty(len(m))
    r[0] = 0
    r[1:len(m)] = m[1:len(m)]-m[0:len(m)-1]
    return r
    
"""
计算BOLL线
"""
def bollLine(k,n):
    mid = ma(k,n)
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

"""绘制k线图"""
def plotK(axs,k,bi,ei):
    for i in range(bi,ei):
        if k[i,1]>k[i,4]:
            c = 'green'
        else:
            c = 'red'
        axs.vlines(i,k[i,3],k[i,2],color=c,zorder=0)
        if k[i,1]>k[i,4]:
            axs.broken_barh([(i-0.4,0.8)],(k[i,1],k[i,4]-k[i,1]),facecolor=c,zorder=1)
        else:
            axs.broken_barh([(i-0.4,0.8)],(k[i,1],k[i,4]-k[i,1]),facecolor="white",edgecolor=c,zorder=1)
            
def plotVLine(axs,x,c):
    for i in x:
        axs.axvline(i,color=c,linestyle='--')
        
"""标注交易点"""
def plotTransPt(axs,n,tr,bi,ei):
    inx = np.logical_and(tr[:,0]>=bi,tr[:,0]<=ei)
    axs[0].scatter(tr[inx,0],tr[inx,2],label='buy',marker=">",s=180,color='red')
    plotVLine(axs[0],tr[inx,0],'red')
    for i in range(1,n+1):
        plotVLine(axs[i],tr[inx,0],'red')
    inx = np.logical_and(tr[:,1]>=bi,tr[:,1]<=ei)
    axs[0].scatter(tr[inx,1],tr[inx,3],label='sell',marker="<",s=180,color='blue')
    plotVLine(axs[0],tr[inx,1],'blue')
    for i in range(1,n+1):
        plotVLine(axs[i],tr[inx,1],'blue')

"""打印交易点"""
def printTrans(k,ma,tr,bi,ei):
    inx = np.logical_and(tr[:,0]>=bi,tr[:,0]<=ei)
    #tr[inx,0] #buy pt
    for ti in tr[inx,0]:
        i = int(ti.item())
        print("buy",i,k[i],ma[i])
    inx = np.logical_and(tr[:,1]>=bi,tr[:,1]<=ei)
    #tr[inx,1] #sell pt
    for ti in tr[inx,1]:
        i = int(ti.item())
        print("sell",i,k[i],ma[i])

def plotVline(axs,v,c,linestyle='--',linewidth=1):
    for i in range(len(axs)):
        axs[i].axvline(v,color=c,linestyle=linestyle,linewidth=linewidth)
        
class MyFormatter(Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0 or math.ceil(x)!=math.floor(x):
            return ''
        return str(self.dates[ind][0])

"""显示K线图，可以组合显示mas,kdj,macd"""
def showKline(k,bi,ei,figsize=(28,16),volume=False,kdate=None,vlines=None,mas=None,boll=False,macd=None,kdj=None,trans=None,errors=None,print=False):
    axsInx = 0
    if macd is not None:
        macdInx = axsInx+1
        axsInx += 1
    if kdj is not None:
        kdjInx = axsInx+1
        axsInx += 1
    if volume:
        volInx = axsInx+1
        axsInx += 1
    ht = [[1],[3,1],[3,1,1],[3,1,1,1],[3,1,1,1,1]]
    widths = [1]
    heights = ht[axsInx]
    gs_kw = dict(width_ratios=widths, height_ratios=heights)
    fig, axs = plt.subplots(axsInx+1, 1,sharex=True,figsize=figsize,gridspec_kw = gs_kw)
    fig.subplots_adjust(hspace=0.02) #调整子图上下间距
    
    if kdate is not None:
        axs[0].xaxis.set_major_formatter(MyFormatter(kdate))
        
    x = np.linspace(bi,ei-1,ei-bi)
    
    if vlines is not None:
        for c in vlines:
            lines = vlines[c]
            for v in lines:
                if v>=bi and v<=ei:
                    plotVline(axs,v,c,linewidth=4 if c=='red' or c=='green' else 1)
    """绘制均线"""                
    if mas is not None:
        ct = {5:"orange",10:"cornflowerblue",20:"pink",30:"salmon",60:"violet",242:"lime"}
        for m in mas:
            xx,alv = maRange(k,m,bi,ei)
            if m in ct:
                axs[0].plot(xx,alv,label="MA"+str(m),color=ct[m])
            else:
                axs[0].plot(xx,alv,label="MA"+str(m))
    """绘制BOLL线"""
    if boll:
        bo = bollLine(k,boll if type(boll)==int else 20)
        axs[0].plot(x,bo[bi:ei,0],label='low',color='magenta') #low
        axs[0].plot(x,bo[bi:ei,1],label='mid',color='royalblue') #mid
        axs[0].plot(x,bo[bi:ei,2],label='upper',color='orange') #upper
    plotK(axs[0],k,bi,ei)
    if volume:
        axs[volInx].step(x, k[bi:ei,0],where='mid',label='volume')
        axs[volInx].plot(x,k[bi:ei,0],label="volume",alpha=0.)
    #axs[0].scatter(x,k[bi:ei+1,4],label="kline",color='orange')
    if trans is not None:
        plotTransPt(axs,axsInx,trans,bi,ei)
        if print:
            printTrans(k,kdj,trans,bi,ei)        
    if errors is not None:
        plotTransPt(axs,axsInx,errors,bi,ei)
        if print:
            printTrans(k,kdj,errors,bi,ei)        
    axs[0].grid(True)

    if macd is not None:
        axs[macdInx].plot(x,macd[bi:ei],label="MACD",color='blue')
        axs[macdInx].axhline(color='black')
        axs[macdInx].grid(True)
    if kdj is not None:
        axs[kdjInx].plot(x,kdj[bi:ei,0],label="K",color='orange')
        axs[kdjInx].plot(x,kdj[bi:ei,1],label="D",color='blue')
        axs[kdjInx].plot(x,kdj[bi:ei,2],label="J",color='purple')
        axs[kdjInx].grid(True)
    fig.autofmt_xdate()
    plt.show()

"""支持翻看K线图"""
def Kline(k,bi,ei,figsize=(28,14),volume=False,kdate=None,vlines=None,mas=None,boll=False,macd=None,kdj=None,trans=None,errors=None,print=False):
    nextbutton = widgets.Button(description="下一页")
    prevbutton = widgets.Button(description="上一页")
    output = widgets.Output()
    
    #display([prevbutton,nextbutton], output)
    #display(nextbutton, output)

    items_layout = Layout( width='auto')     # override the default width of the button to 'auto' to let the button grow

    box_layout = Layout(display='flex',
                        flex_flow='row',
                        align_items='stretch',
                        border='solid',
                        width='50%')

    words = ['correct', 'horse', 'battery', 'staple']
    items = [prevbutton,nextbutton]
    box = Box(children=items, layout=box_layout)
    
    beginPT = bi
    endPT = ei
    showRange = ei-bi
    
    def on_nextbutton_clicked(b):
        nonlocal beginPT,endPT,showRange
        beginPT += showRange
        endPT += showRange
        if endPT >= len(k):
            endPT = len(k)
            beginPT = endPT-showRange        
        output.clear_output(wait=True)
        with output:
            showKline(k,beginPT,endPT,figsize=figsize,volume=volume,kdate=kdate,vlines=vlines,mas=mas,boll=boll,macd=macd,kdj=kdj,trans=trans,errors=errors)
    
    def on_prevbutton_clicked(b):
        nonlocal beginPT,endPT,showRange
        beginPT -= showRange
        endPT -= showRange
        if beginPT < 0 :
            endPT = showRange
            beginPT = 0
        output.clear_output(wait=True)        
        with output:
            showKline(k,beginPT,endPT,figsize=figsize,volume=volume,kdate=kdate,vlines=vlines,mas=mas,boll=boll,macd=macd,kdj=kdj,trans=trans,errors=errors)
            
    nextbutton.on_click(on_nextbutton_clicked)
    prevbutton.on_click(on_prevbutton_clicked)
    
    display(box,output)
    with output:
        showKline(k,beginPT,endPT,figsize=figsize,volume=volume,kdate=kdate,vlines=vlines,mas=mas,boll=boll,macd=macd,kdj=kdj,trans=trans,errors=errors)

"""
计算MACD周期内的最低点和最高点
m 为macd数组
返回最低点的数组，最高点数组
"""
def MacdBestPt(k,m):
    minpts = []
    maxpts = []
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
            else:
                maxpts.append(maxi)
            minx = k[i,3]
            mini = i
            maxx = k[i,2]
            maxi = i
        prev = m[i]
    return np.array(minpts),np.array(maxpts)        
    