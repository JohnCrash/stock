import stock
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import math
import ipywidgets as widgets
from IPython.display import display
from ipywidgets import Layout, Button, Box
import time

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
    kdate : 日期表
    vlines : {} 竖线
    trans : 交易点
    figsize : (w,h)
    debug : True or False 打印调试信息
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
        if 'ma' in self._config:
            self._showma = True
        if 'macd' in self._config and self._config['macd']:
            self._macdInx = self._axsInx+1
            self._axsInx += 1
            self._macd,_ = stock.macd(self._k)
            self._showmacd = True
        if 'kdj' in self._config and self._config['kdj'] is not None:
            self._kdjInx = self._axsInx+1
            self._axsInx += 1
            self._kdj = stock.kdj(self._k,self._config['kdj'])
            self._showkdj = True
        if 'volume' in self._config and self._config['volume']:
            self._volInx =self._axsInx+1
            self._axsInx += 1
            self._volumeboll = stock.boll(self._k[:,0],20)
            self._showvolume = True
        self._widths = [1]
        self._heights = [3]
        for i in range(self._axsInx):
            self._heights.append(1)
        if 'boll' in self._config:            
            self._boll = stock.bollLineK(self._k,self._config['boll'])
            self._showboll = True
        if 'vlines' in self._config:
            self._showvlines = True
        if 'best' in self._config and self._config['best']:
            if self._showmacd:
                self._minpt,self._maxpt = stock.MacdBestPt(self._k,self._macd)
            else:
                macd,_ = stock.macd(self._k)
                self._minpt,self._maxpt = stock.MacdBestPt(self._k,macd)
            self._showbest = True

    #company可以是kline数据，可以是code，也可以是公司名称
    def __init__(self,company,period='d',config={}):
        self._config = {"boll":20,"macd":True,"volume":True,"debug":False}
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
        self.config(config)
        self._backup = self._config

    def enable(self,k):
        if k=='ma':
            if 'ma' in self._backup:
                self._config['ma'] = self._backup['ma']
            else:
                self._config['ma'] = [5,10,20,30,60]
        elif k=='macd':
            self._config['macd'] = True
        elif k=='boll':
            if 'boll' in self._backup:
                self._config['boll'] = self._backup['boll']
            else:
                self._config['boll'] = 20
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
        self.config()

    def disable(self,k):
        del self._config[k]
        self.config()

    #显示K线图
    def showKline(self,bi=None,ei=None,figsize=(30,16)):
        if bi is None:
            bi = len(self._k)-self._showcount
        if ei is None:
            ei = len(self._k)
        gs_kw = dict(width_ratios=self._widths, height_ratios=self._heights)
        fig, axs = plt.subplots(self._axsInx+1, 1,sharex=True,figsize=figsize,gridspec_kw = gs_kw)
        fig.subplots_adjust(hspace=0.02) #调整子图上下间距
        
        if self._date is not None:
            axs[0].xaxis.set_major_formatter(MyFormatter(self._date))
        
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
        for i in range(self._axsInx+1):
            axs[i].set_xlim(bi,ei)
            axs[i].set_xticks(xticks)

        x = np.linspace(bi,ei-1,ei-bi)
        #绘制一系列的竖线贯彻整个图例
        if self._showvlines:
            vlines = self._config['vlines']
            for c in vlines:
                lines = vlines[c]
                for v in lines:
                    if v>=bi and v<=ei:
                        plotVline(axs,v,c,linewidth=4 if c=='red' or c=='green' else 1)
        if self._showbest:
            for v in self._minpt:
                if v>=bi and v<=ei:
                    plotVline(axs,v,'green',linewidth=4)
            for v in self._maxpt:
                if v>=bi and v<=ei:
                    plotVline(axs,v,'red',linewidth=4)

        """绘制均线"""                
        if self._showma:
            ct = {5:"orange",10:"cornflowerblue",20:"pink",30:"salmon",60:"violet",242:"lime"}
            for m in self._config['ma']:
                xx,alv = stock.maRangeK(self._k,m,bi,ei)
                if m in ct:
                    axs[0].plot(xx,alv,label="MA"+str(m),color=ct[m])
                else:
                    axs[0].plot(xx,alv,label="MA"+str(m))
        """绘制BOLL线"""
        if self._showboll:
            axs[0].plot(x,self._boll[bi:ei,0],label='low',color='magenta') #low
            axs[0].plot(x,self._boll[bi:ei,1],label='mid',color='royalblue') #mid
            axs[0].plot(x,self._boll[bi:ei,2],label='upper',color='orange') #upper

        axs[0].set_title('%s %s'%(self._company[2],self._company[1]))
        plotK(axs[0],self._k,bi,ei)

        if self._showvolume:
            axs[self._volInx].step(x, self._k[bi:ei,0],where='mid',label='volume')
            axs[self._volInx].plot(x,self._k[bi:ei,0],label="volume",alpha=0.)
            axs[self._volInx].plot(x,self._volumeboll[bi:ei,0],label='low',color='magenta') #low
            axs[self._volInx].plot(x,self._volumeboll[bi:ei,1],label='low',color='red') #mid
            axs[self._volInx].plot(x,self._volumeboll[bi:ei,2],label='upper',color='orange') #upper            
            axs[self._volInx].grid(True)

        if 'trans' in self._config:
            plotTransPt(axs,self._axsInx,self._config['trans'],bi,ei) 
      
        axs[0].grid(True)

        if self._showmacd:
            axs[self._macdInx].plot(x,self._macd[bi:ei],label="MACD",color='blue')
            axs[self._macdInx].axhline(color='black')
            axs[self._macdInx].grid(True)
        if self._showkdj:
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,0],label="K",color='orange')
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,1],label="D",color='blue')
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,2],label="J",color='purple')
            axs[self._kdjInx].grid(True)
        fig.autofmt_xdate()
        plt.show()

    def show(self,bi=None,ei=None,figsize=(30,14)):
        if bi is None:
            bi = len(self._k)-self._showcount
        if ei is None:
            ei = len(self._k)        
        nextbutton = widgets.Button(description="下一页")
        prevbutton = widgets.Button(description="上一页")
        bolltoggle = widgets.ToggleButton(
            value=self._showboll,
            description='BOLL',
            disabled=False,
            button_style='',
            tooltip='BOLL线',
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
        output = widgets.Output()

        items_layout = Layout( width='auto')     # override the default width of the button to 'auto' to let the button grow

        box_layout = Layout(display='flex',
                            flex_flow='row',
                            align_items='stretch',
                            border='solid',
                            width='100%')

        words = ['correct', 'horse', 'battery', 'staple']
        items = [prevbutton,nextbutton,bolltoggle,matoggle,volumetoggle,macdtoggle,kdjtoggle,besttoggle]
        box = Box(children=items, layout=box_layout)
        
        beginPT = bi
        endPT = ei
        showRange = ei-bi
        
        def on_nextbutton_clicked(b):
            nonlocal beginPT,endPT,showRange
            beginPT += showRange
            endPT += showRange
            if endPT >= len(self._k):
                endPT = len(self._k)
                beginPT = endPT-showRange        
            output.clear_output(wait=True)
            with output:
                self.showKline(beginPT,endPT,figsize=figsize)
        
        def on_prevbutton_clicked(b):
            nonlocal beginPT,endPT,showRange
            beginPT -= showRange
            endPT -= showRange
            if beginPT < 0 :
                endPT = showRange
                beginPT = 0
            output.clear_output(wait=True)        
            with output:
                self.showKline(beginPT,endPT,figsize=figsize)
        
        def on_change(event):
            source = event['owner']
            if event['new']:
                self.enable(source.description.lower())
            else:
                self.disable(source.description.lower())
            output.clear_output(wait=True)
            with output:
                self.showKline(beginPT,endPT,figsize=figsize)

        nextbutton.on_click(on_nextbutton_clicked)
        prevbutton.on_click(on_prevbutton_clicked)
        bolltoggle.observe(on_change,names='value')
        matoggle.observe(on_change,names='value')
        volumetoggle.observe(on_change,names='value')
        macdtoggle.observe(on_change,names='value')
        kdjtoggle.observe(on_change,names='value')
        besttoggle.observe(on_change,names='value')
        display(box,output)
        with output:
            self.showKline(beginPT,endPT,figsize=figsize)
