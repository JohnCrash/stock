import stock
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import math
import ipywidgets as widgets
from IPython.display import display
from ipywidgets import Layout, Button, Box
import time
import trend

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

def plotVLine(axs,x,c):
    for i in x:
        axs.axvline(i,color=c,linestyle='--')

def plotVline(axs,v,c,linestyle='-',linewidth=1):
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
        t = self.dates[ind][0]
        return '%s-%s-%s'%(t.year,t.month,t.day)
"""kline 图显示"""
"""
config {
    ma : [5,10,20,...]
    kdj : n
    volume : True or False
    macd : True or False
    boll : n
    trend: True or False #趋势线
    kdate : 日期表
    vlines : {} 竖线
    trans : 交易点
    figsize : (w,h)
    debug : True or False 打印调试信息
    figure : [[ 额外的图例
        {
            name
            color
            linewidth
            linestyle
            data
        },
        ...
    ],...]
    cb : function(self,axs,bi,ei)
}
"""
class Plote:
    def config(self,config={}):
        for k in config:
            self._config[k] = config[k]
        self._axsInx = 0
        self._showma = False
        self._showmacd = False
        self._showkdj = False
        self._showvolume = False
        self._showboll = False
        self._showvlines = False
        self._showbest = False
        self._showfigure = False
        self._showbollwidth = False
        self._showtrend = False
        if 'ma' in self._config:
            self._showma = True
        if 'figure' in self._config:
            self._figureInx = []
            for f in self._config['figure']:
                self._figureInx.append(self._axsInx+1)
                self._axsInx += 1
            self._showfigure = True

        if 'boll' in self._config:            
            self._boll = stock.bollLineK(self._k,self._config['boll'])
            self._showboll = True
        if 'trend' in self._config and self._config['trend']:
            macd,_ = stock.macd(self._k)
            self._trend = trend.fractal(self._k,0.2)
            self._trend2 = trend.fractal(self._k,0.8)
            self._showtrend = True

        if 'bollwidth' in self._config and self._config['bollwidth']:
            self._bollwidthInx = self._axsInx+1
            self._axsInx += 1
            self._showbollwidth = True
            self._bollwidth = stock.bollWidth(self._boll)

        if 'macd' in self._config and self._config['macd']:
            self._macdInx = self._axsInx+1
            self._axsInx += 1
            #防止计算两边macd
            if self._showtrend:
                self._macd = macd
            else:
                self._macd,_ = stock.macd(self._k)
            self._showmacd = True
        if 'kdj' in self._config and self._config['kdj'] is not None:
            self._kdjInx = self._axsInx+1
            self._axsInx += 1
            if type(self._config['kdj'])==int:
                self._kdj = stock.kdjK(self._k,self._config['kdj'])
            elif type(self._config['kdj'])==np.ndarray:
                self._kdj = self._config['kdj']
            self._showkdj = True
        if 'volume' in self._config and self._config['volume']:
            self._volInx =self._axsInx+1
            self._axsInx += 1
            self._volumeboll = stock.boll(self._k[:,0],20)
            self._showvolume = True
        #将大盘指数的收盘价显示在图表中
        
        self._widths = [1]
        self._heights = [3]
        for i in range(self._axsInx):
            self._heights.append(1)
        if 'vlines' in self._config:
            self._showvlines = True
        if 'best' in self._config and self._config['best']:
            if self._showmacd:
                self._minpt,self._maxpt,_ = stock.MacdBestPt(self._k,self._macd)
            else:
                macd,_ = stock.macd(self._k)
                self._minpt,self._maxpt,_ = stock.MacdBestPt(self._k,macd)
            self._showbest = True


    #company可以是kline数据，可以是code，也可以是公司名称
    def __init__(self,company,period='d',config={}):
        self._config = {"boll":20,"bollwidth":0.2,"macd":True,"volume":True,"trend":True,"debug":False}
        self._period = period
        if self._period=='d':
            self._showcount = 120
        elif int(self._period)==5: #48
            self._showcount = 144
        elif int(self._period)==15: #16
            self._showcount = 112
        elif int(self._period)==60: #4
            self._showcount = 120
        else:
            self._showcount = 120
        if type(company)==np.ndarray:
            self._k = company
            self._company = None
            self._date = None
        elif type(company)==str:
            self._company,self._k,self._date = stock.loadKline(company,self._period)
        #将大盘指数画在图表中            
        if "index" in self._config and self._config["index"] and self._company[1] != 'SZ399001' and self._company[1] != 'SH000001':
            #这里做日期对齐
            _,szk,szd = stock.loadKline('SZ:399001',self._period)
            K = np.zeros((len(self._k)))
            j = 0
            for i in range(len(self._date)):
                for k in range(j,len(szd)-i):
                    if szd[i+k][0] == self._date[i][0]:
                        K[i] = szk[i+k,4]
                        j = k
                        break
            self._szclose = K
        else:
            self._szclose = None
        self.config(config)
        self._backup = self._config.copy()

    def enable(self,k):
        if k=='ma':
            if 'ma' in self._backup:
                self._config['ma'] = self._backup['ma']
            else:
                self._config['ma'] = [5,10,20,30,60]
        elif k=='trend':
            self._config['trend'] = True
        elif k=='macd':
            self._config['macd'] = True
        elif k=='boll':
            if 'boll' in self._backup:
                self._config['boll'] = self._backup['boll']
            else:
                self._config['boll'] = 20
        elif k=='bollwidth':
            if 'bollwidth' in self._backup:
                self._config['bollwidth'] = self._backup['bollwidth']
            else:
                self._config['bollwidth'] = 0.2
        elif k=='kdj':
            if 'kdj' in self._backup:
                self._config['kdj'] = self._backup['kdj']
            else:
                self._config['kdj'] = 9
        elif k=='vlines':
            if 'vlines' in self._backup:
                self._config['vlines'] = self._backup['vlines']
            else:
                self._config['vlines'] = []
        elif k=='volume':
            self._config['volume'] = True
        elif k=='best':
            self._config['best'] = True
        elif k=='figure':
            if 'figure' in self._backup:
                self._config['figure'] = self._backup['figure']
        self.config()

    def disable(self,k):
        del self._config[k]
        self.config()

    #给出时间返回索引
    def date2index(self,d):
        for i in range(len(self._date)):
            if d == self._date[i][0]:
                return i
        return 0
    
    def index2date(self,i):
        if i>=len(self._date):
            return self._date[-1][0]
        else:
            return self._date[i][0]

    #显示K线图
    def showKline(self,bi=None,ei=None,figsize=(30,16)):
        if bi is None:
            bi = len(self._k)-self._showcount
        if ei is None:
            ei = len(self._k)
        gs_kw = dict(width_ratios=self._widths, height_ratios=self._heights)
        fig, axs = plt.subplots(self._axsInx+1, 1,sharex=True,figsize=figsize,gridspec_kw = gs_kw)
        fig.subplots_adjust(hspace=0.02) #调整子图上下间距
        axsK = axs if self._axsInx==0 else axs[0]
        if self._date is not None:
            axsK.xaxis.set_major_formatter(MyFormatter(self._date))
        #时间坐标网格线，天的画在星期一，其他的以天为单位
        if self._period=='d':
            if self._date is not None:
                xticks = []
                for i in range(bi,ei):
                    if self._date[i][0].weekday()==0:
                        xticks.append(i)
                xticks = np.array(xticks)
            else:
                xticks = np.arange(bi,ei,10)
        else:
            if int(self._period) == 15:
                xticks = np.arange(bi,ei,16)
            elif int(self._period) == 5:
                xticks = np.arange(bi,ei,48)
            elif int(self._period) == 60:
                xticks = np.arange(bi,ei,4)

        if self._axsInx==0:
            axsK.set_xlim(bi,ei)
            axsK.set_xticks(xticks)
            axsK.grid(True)
        else:
            for i in range(self._axsInx+1):
                axs[i].set_xlim(bi,ei)
                axs[i].set_xticks(xticks)
                axs[i].grid(True)

        x = np.linspace(bi,ei-1,ei-bi)
        #绘制一系列的竖线贯彻整个图例
        if self._showvlines:
            vlines = self._config['vlines']
            for lines in vlines:
                for v in lines['x']:
                    if v>=bi and v<=ei:
                        plotVline(axs,v,lines['color'] if 'color' in lines else 'blue',
                        linewidth=lines['linewidth'] if 'linewidth' in lines else 1,
                        linestyle=lines['linestyle'] if 'linestyle' in lines else '-',)
        #绘制bollwidth
        if self._showbollwidth:
            axs[self._bollwidthInx].plot(x,self._bollwidth[bi:ei],color='red',linewidth=2)
            axs[self._bollwidthInx].axhline(self._config['bollwidth'],color='black') 
            axs[self._bollwidthInx].axhline(0.1,color='green') 
        #绘制macd最佳买卖点
        if self._showbest:
            for v in self._minpt:
                if v>=bi and v<=ei:
                    plotVline(axs,v,'green',linewidth=4,linestyle='-.')
            for v in self._maxpt:
                if v>=bi and v<=ei:
                    plotVline(axs,v,'red',linewidth=4,linestyle='-.')

        """绘制均线"""                
        if self._showma:
            ct = {5:"orange",10:"cornflowerblue",20:"pink",30:"salmon",60:"violet",242:"lime"}
            for m in self._config['ma']:
                xx,alv = stock.maRangeK(self._k,m,bi,ei)
                if m in ct:
                    axsK.plot(xx,alv,label="MA"+str(m),color=ct[m])
                else:
                    axsK.plot(xx,alv,label="MA"+str(m))
        """绘制BOLL线"""
        if self._showboll:
            axsK.plot(x,self._boll[bi:ei,0],label='low',color='magenta') #low
            axsK.plot(x,self._boll[bi:ei,1],label='mid',color='royalblue') #mid
            axsK.plot(x,self._boll[bi:ei,2],label='upper',color='orange') #upper
        #绘制趋势线
        if self._showtrend:
            for line in self._trend:
                if line[1]>bi and line[0]<ei:
                    x0 = line[0]
                    x1 = line[1]
                    k = line[2]
                    b = line[3]
                    axsK.plot([x0,x1],[k*x0+b,k*x1+b],color='red' if k>0 else 'green',linewidth=2)
            for line in self._trend2:
                if line[1]>bi and line[0]<ei:
                    x0 = line[0]
                    x1 = line[1]
                    k = line[2]
                    b = line[3]
                    axsK.plot([x0,x1],[k*x0+b,k*x1+b],color='red' if k>0 else 'green',linewidth=4)                    
        if self._company is not None:
            axsK.set_title('%s %s'%(self._company[2],self._company[1]))
        #绘制k线图
        plotK(axsK,self._k,bi,ei)
        #将大盘数据绘制在K线图上
        if self._szclose is not None:
            kmax = self._k[bi:ei,1:4].max()
            kmin = self._k[bi:ei,1:4].min()  
            szkmax = self._szclose[bi:ei].max()
            szkmin = self._szclose[bi:ei].min()
            axsK.plot(x,(self._szclose[bi:ei]-szkmin)*(kmax-kmin)/(szkmax-szkmin)+kmin,color='red',linewidth=2,alpha=0.5)
        #绘制成交量
        if self._showvolume:
            axs[self._volInx].step(x, self._k[bi:ei,0],where='mid',label='volume')
            axs[self._volInx].plot(x,self._k[bi:ei,0],label="volume",alpha=0.)
            axs[self._volInx].plot(x,self._volumeboll[bi:ei,0],label='low',color='magenta') #low
            axs[self._volInx].plot(x,self._volumeboll[bi:ei,1],label='low',color='red') #mid
            axs[self._volInx].plot(x,self._volumeboll[bi:ei,2],label='upper',color='orange') #upper 
            axs[self._volInx].axhline(color='black')           
            axs[self._volInx].grid(True)
        #绘制交易点
        if 'trans' in self._config:
            plotTransPt(axs,self._axsInx,self._config['trans'],bi,ei) 
      
        axsK.grid(True)
        #绘制macd
        if self._showmacd:
            axs[self._macdInx].plot(x,self._macd[bi:ei],label="MACD",color='blue')
            axs[self._macdInx].axhline(color='black')
        #绘制kdj
        if self._showkdj:
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,0],label="K",color='orange')
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,1],label="D",color='blue')
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,2],label="J",color='purple')
        #绘制额外的图表
        if self._showfigure:
            i = 0
            for f in self._config['figure']:
                axsinx = self._figureInx[i]
                for p in f:
                    if 'data' in p:
                        axs[axsinx].plot(x,p['data'][bi:ei],
                        label=p['name'] if 'name' in p else '',
                        color=p['color'] if 'color' in p else 'blue',
                        linewidth=p['linewidth'] if 'linewidth' in p else 1,
                        linestyle=p['linestyle'] if 'linestyle' in p else '-'
                        )
                i+=1
        #一个从外部进行调整图表的手段                
        if 'cb' in self._config:
            self._config['cb'](self,axs,bi,ei)
        fig.autofmt_xdate()
        plt.show()

    #code2另一只股票，进行比较显示
    def show(self,bi=None,ei=None,code2=None,figsize=(30,14)):
        if bi is None:
            bi = len(self._k)-self._showcount
        if ei is None:
            ei = len(self._k)
        if code2 is not None:
            figsize = (30,8)
            figure2 = Plote(code2,self._period)
        else:
            figure2 = None
        nextbutton = widgets.Button(description="下一页")
        prevbutton = widgets.Button(description="上一页")
        zoominbutton = widgets.Button(description="+")
        zoomoutbutton = widgets.Button(description="-")
        bolltoggle = widgets.ToggleButton(
            value=self._showboll,
            description='BOLL',
            disabled=False,
            button_style='',
            tooltip='BOLL线',
            icon='check')
        trendtoggle = widgets.ToggleButton(
            value=self._showtrend,
            description='trend',
            disabled=False,
            button_style='',
            tooltip='趋势线',
            icon='check')              
        bollwidthtoggle = widgets.ToggleButton(
            value=self._showbollwidth,
            description='BOLLWIDTH',
            disabled=False,
            button_style='',
            tooltip='BOLL宽度',
            icon='check')            
        matoggle = widgets.ToggleButton(
            value=self._showma,
            description='MA',
            disabled=False,
            button_style='',
            tooltip='均线',
            icon='check')
        volumetoggle = widgets.ToggleButton(
            value=self._showvolume,
            description='VOLUME',
            disabled=False,
            button_style='',
            tooltip='成交量',
            icon='check')            
        macdtoggle = widgets.ToggleButton(
            value=self._showmacd,
            description='MACD',
            disabled=False,
            button_style='',
            tooltip='MACD',
            icon='check')     
        kdjtoggle = widgets.ToggleButton(
            value=self._showkdj,
            description='KDJ',
            disabled=False,
            button_style='',
            tooltip='KDJ',
            icon='check')
        besttoggle = widgets.ToggleButton(
            value=self._showbest,
            description='BEST',
            disabled=False,
            button_style='',
            tooltip='BEST',
            icon='check')
        if self._showfigure:
            figuretoggle = widgets.ToggleButton(
                value=self._showfigure,
                description='FIGURE',
                disabled=False,
                button_style='',
                tooltip='FIGURE',
                icon='check')                               
        output = widgets.Output()

        items_layout = Layout( width='auto')     # override the default width of the button to 'auto' to let the button grow

        box_layout = Layout(display='flex',
                            flex_flow='row',
                            align_items='stretch',
                            border='solid',
                            width='100%')

        words = ['correct', 'horse', 'battery', 'staple']
        items = [prevbutton,nextbutton,zoominbutton,zoomoutbutton,bolltoggle,bollwidthtoggle,trendtoggle,matoggle,volumetoggle,macdtoggle,kdjtoggle,besttoggle]
        if self._showfigure:
            items.append(figuretoggle)
        box = Box(children=items, layout=box_layout)
        
        beginPT = bi
        endPT = ei
        showRange = ei-bi
        
        def showline():
            output.clear_output(wait=True)
            with output:
                self.showKline(beginPT,endPT,figsize=figsize)
                if figure2 is not None:
                    bi = figure2.date2index( self.index2date(beginPT) )
                    ei = figure2.date2index( self.index2date(endPT) )
                    if bi != ei:
                        figure2.showKline(bi,ei,figsize=figsize)


        def on_nextbutton_clicked(b):
            nonlocal beginPT,endPT,showRange
            beginPT += showRange
            endPT += showRange
            if endPT >= len(self._k):
                endPT = len(self._k)
                beginPT = endPT-showRange        
            showline()
        
        def on_prevbutton_clicked(b):
            nonlocal beginPT,endPT,showRange
            beginPT -= showRange
            endPT -= showRange
            if beginPT < 0 :
                endPT = showRange
                beginPT = 0
            showline()

        def on_zoomin(b):
            nonlocal beginPT,endPT,showRange
            showRange = math.floor(showRange/2)
            beginPT = endPT - showRange
            showline()

        def on_zoomout(b):
            nonlocal beginPT,endPT,showRange
            showRange *= 2
            beginPT = endPT - showRange
            if beginPT < 0:
                beginPT = 0
                endPT = beginPT+showRange
            showline()

        def on_change(event):
            source = event['owner']
            if event['new']:
                self.enable(source.description.lower())
            else:
                self.disable(source.description.lower())
            showline()

        nextbutton.on_click(on_nextbutton_clicked)
        prevbutton.on_click(on_prevbutton_clicked)

        zoominbutton.on_click(on_zoomin)
        zoomoutbutton.on_click(on_zoomout)

        trendtoggle.observe(on_change,names='value')
        bolltoggle.observe(on_change,names='value')
        bollwidthtoggle.observe(on_change,names='value')
        matoggle.observe(on_change,names='value')
        volumetoggle.observe(on_change,names='value')
        macdtoggle.observe(on_change,names='value')
        kdjtoggle.observe(on_change,names='value')
        besttoggle.observe(on_change,names='value')
        if self._showfigure:
            figuretoggle.observe(on_change,names='value')

        display(box,output)
        with output:
            self.showKline(beginPT,endPT,figsize=figsize)
            if figure2 is not None:
                bi = figure2.date2index( self.index2date(beginPT) )
                ei = figure2.date2index( self.index2date(endPT) )
                if bi != ei:
                    figure2.showKline(bi,ei,figsize=figsize)

