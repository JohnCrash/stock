import stock
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import math
import ipywidgets as widgets
from IPython.display import display,update_display,clear_output
from ipywidgets import Layout, Button, Box
from datetime import date,datetime,timedelta
import time
import trend
import  warnings
import xueqiu
import uuid
#定制show
from matplotlib._pylab_helpers import Gcf
from ipykernel.pylab.backend_inline import _fetch_figure_metadata,show

warnings.filterwarnings("ignore", module="matplotlib")

def plt_show(display_id,isupdate):
    try:
        for figure_manager in Gcf.get_all_fig_managers():
            if isupdate:
                update_display(
                    figure_manager.canvas.figure,
                    metadata=_fetch_figure_metadata(figure_manager.canvas.figure),
                    display_id=display_id
                )                
            else:
                display(
                    figure_manager.canvas.figure,
                    metadata=_fetch_figure_metadata(figure_manager.canvas.figure),
                    display_id=display_id
                )
    finally:
        show._to_draw = []
        # only call close('all') if any to close
        # close triggers gc.collect, which can be slow
        if Gcf.get_all_fig_managers():
            plt.close('all')

"""绘制k线图"""
def plotK(axs,k,bi,ei):
    for i in range(bi,ei):
        if k[i,1]>k[i,4]:
            c = 'green'
        else:
            c = 'red'
        axs.vlines(i,k[i,3],k[i,2],color=c,zorder=0)
        #对涨停和跌停加粗标注
        if i>0 and abs((k[i,4]-k[i-1,4])/k[i-1,4])>=0.097:
            lw = 4
            fc = "white"
        else:
            lw = 1
            fc = c
        if k[i,1]>k[i,4]:
            axs.broken_barh([(i-0.4,0.8)],(k[i,1],k[i,4]-k[i,1]),facecolor=fc,edgecolor=c,zorder=1,linewidth=lw)
        else:
            axs.broken_barh([(i-0.4,0.8)],(k[i,1],k[i,4]-k[i,1]),facecolor="white",edgecolor=c,zorder=1,linewidth=lw)
  
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
    def __init__(self, dates,period,fmt='%Y-%m-%d'):
        self.dates = dates
        self.period = period
        if type(period)==str:
            self.fmt = fmt
        else:
            self.fmt = '%Y-%m-%d %h:%M'

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0 or math.ceil(x)!=math.floor(x):
            return ''

        t = self.dates[ind][0]
        if type(self.period)==str:
            return '%s-%s-%s'%(t.year,t.month,t.day)
        else:
            return '%s-%s-%s %s:%s'%(t.year,t.month,t.day,t.hour,t.minute)
"""kline 图显示"""
"""
config {
    ma : [5,10,20,...]
    kdj : n
    volume : True or False
    macd : True or False
    boll : n
    energy: True or False #能量线
    trend: True or False #趋势线
    volumeprices:True #量价关系
    kdate : 日期表
    vlines : [{
        x : []
        dates:[]
        color,
        linewidth
        linestyle
    }] 竖线
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
    figure: callback figure(self,)返回figure
    cb : function(self,axs,bi,ei)
    lightweight: True or False 如果是True仅仅加载一年的数据
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
        self._showenergy = False
        if len(self._k)==0: #完全没有数据
            return
        if 'ma' in self._config:
            self._showma = True
        if 'figure' in self._config:
            self._figureInx = []
            if type(self._config['figure'])==dict:
                figures = self._config['figure']
            elif callable(self._config['figure']):
                figures = self._config['figure'](self)
            for f in figures:
                self._figureInx.append(self._axsInx+1)
                self._axsInx += 1
            self._showfigure = True
        if 'boll' in self._config:            
            self._boll = stock.bollLineK(self._k,self._config['boll'])
            self._showboll = True
        if 'trend' in self._config and self._config['trend']:
            macd = stock.macd(self._k)
            self._macd = macd
            self._trend = trend.macdTrend(self._k,self._macd)
            #self._trend2 = trend.large(self._k,self._trend,0.15)
            if self._date and 'markpos' in self._config:
                dd = self._config['markpos']
                self._trendHeadPos = len(self._k)-1
                for i in range(len(self._date)):
                    if self._date[i][0] == dd:
                        self._trendHeadPos = i
                        break
            else:
                self._trendHeadPos = len(self._k)-1
            self._showtrend = True
        if 'energy' in self._config and self._config['energy']:
            self._energyInx = self._axsInx+1
            self._axsInx += 1
            if self._correcttionVolume and (self._period==5 or self._period==15 or self._period==30 or self._period==60 or self._period==120 or self._period==1):
                volume = stock.correctionVolume(self._k,self._date,self._period)
                self._volumeenergy = stock.kdj(stock.volumeEnergy(volume))[:,2]
                self._volumekdj = stock.kdj(volume)[:,2]
                self._k = np.array(self._k,copy=True)
                self._k[:,0] = volume
            else:
                self._volumeenergy = stock.kdj(stock.volumeEnergyK(self._k))[:,2]
                self._volumekdj = stock.kdj(self._k[:,0])[:,2]
            self._showenergy = True
        if 'bollwidth' in self._config and self._config['bollwidth']:
            self._bollwidthInx = self._axsInx+1
            self._axsInx += 1
            self._showbollwidth = True
            self._bollwidth = stock.bollWidth(self._boll)

        if 'macd' in self._config and self._config['macd']:
            self._macdInx = self._axsInx+1
            self._axsInx += 1
            #防止计算两边macd
            if not self._showtrend:
                self._macd = stock.macd(self._k)
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
            #支持使用日期
            vlines = self._config['vlines']
            for lines in vlines:
                if 'dates' in lines:
                    lines['x'] = []
                    for d in lines['dates']:
                        lines['x'].append(self.date2index(d))
            self._showvlines = True
        if 'best' in self._config and self._config['best']:
            if self._showmacd:
                self._minpt,self._maxpt,_ = stock.MacdBestPt(self._k,self._macd)
            else:
                if not self._showtrend:
                    self._macd = stock.macd(self._k)
                self._minpt,self._maxpt,_ = stock.MacdBestPt(self._k,self._macd)
            self._showbest = True

    def switchweek(self):
        self._period = 'w'
        self.reload()
        self.config()
    def switchday(self):
        self.init(self._comarg,'d',self._config)
        self.config()
    """
    对不同基本的数据留有缓存
    """
    def getKlineData(self,code,period):
        if len(code)>3 and code[2]==':':
            code = code.replace(':','')
        if not (code in self._cacheK and period in self._cacheK[code]):
            if period == 'w':
                after = None #全部数据
            elif period == 'd':
                after = stock.dateString(date.today()-timedelta(days=5*365)) #5年数据
            else:
                after = stock.dateString(date.today()-timedelta(days=60))

            c,k,d = stock.loadKline(code,period,after=after)
            self._cacheK[code] = {}
            self._cacheK[code][period] = (c,k,d,after)
        
        cur = self._cacheK[code][period]
        _,k,d = xueqiu.appendK(code,period,cur[1],cur[2])
        return cur[0],k,d

    def init(self,company,period,config,date_ = None,companyInfo=None):
        self._period = period
        if self._period=='d' or self._period=='w':
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
            self._company = companyInfo
            self._comarg = companyInfo[1] #code
            self._date = date_
        elif type(company)==str:
            if self._period == 'w': #周线
                self._company,k,d = self.getKlineData(company,'d')
                self._k,self._date = stock.weekK(k,d)
            else:
                self._company,self._k,self._date = self.getKlineData(company,self._period)
        if len(self._k)==0: #完全没有数据不进行进一步处理
            return
        #将大盘指数画在图表中   
        if "index" in config and config["index"] and self._company[1] != 'SZ399001' and self._company[1] != 'SH000001':
            #这里做日期对齐
            if self._period=='w':
                _,szk,szd = self.getKlineData('SZ399001','d')
                K = stock.alignK(self._date,szk,szd)
                WK,WD = stock.weekK(K,self._date)
                self._szclose = WK[:,4]
                self._szvolumekdj = stock.kdj(WK[:,0])[:,2]
                self._szvolumeenergy = stock.kdj(stock.volumeEnergyK(WK))[:,2]
                self._szmacd = stock.macd(WK)
            else:
                _,szk,szd = self.getKlineData('SZ399001',self._period)
                K = stock.alignK(self._date,szk,szd)
                self._szclose = K[:,4]
                self._szvolumekdj = stock.kdj(K[:,0])[:,2]
                self._szvolumeenergy = stock.kdj(stock.volumeEnergyK(K))[:,2]
                self._szmacd = stock.macd(K)
        else:
            self._szclose = None

    #重新加载对象数据all=True加载全部数据,all=False更新数据
    def reload(self,all=True):
        self.init(self._comarg,self._period,self._config)
        self.config()
    
    def __del__(self):
        if self._timer is not None:
            self._timer.cancel()

    #company可以是kline数据，可以是code，也可以是公司名称
    def __init__(self,company,period='d',config={},date=None,companyInfo=None):
        self._timer = None
        self._correcttionVolume = False
        self._cacheK = {}
        self._configarg = config
        self._comarg = company
        self._datearg = date
        self._companyInfoarg = companyInfo
        self._display_id = str(uuid.uuid1())
        self._isupdate = False
        self._config = {"macd":True,"energy":True,"volume":True,"trend":True,"ma":[20],"debug":False,"volumeprices":True} #"bollwidth":0.2,
        self.init(company,period,config,date,companyInfo=companyInfo)
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
        elif k=='energy':
            self._config['energy'] = True
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

    def disable(self,k):
        if k in self._config:
            del self._config[k]

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
        if bi>0:
            if bi>len(self._k):
                bi = len(self._k)-1
        else:
            if bi<=-len(self._k):
                bi = -len(self._k)+1
        if ei>0:
            if ei>len(self._k):
                ei = len(self._k)
        else:
            if ei<=-len(self._k):
                ei = -len(self._k)+1
        gs_kw = dict(width_ratios=self._widths, height_ratios=self._heights)
        fig, axs = plt.subplots(self._axsInx+1, 1,sharex=True,figsize=figsize,gridspec_kw = gs_kw)
        fig.subplots_adjust(hspace=0.02) #调整子图上下间距
        axsK = axs if self._axsInx==0 else axs[0]
        if self._date is not None:
            axsK.xaxis.set_major_formatter(MyFormatter(self._date,self._period))
        #时间坐标网格线，天的画在星期一，其他的以天为单位
        if self._period=='d' or self._period=='w':
            if self._date is not None:
                xticks = []
                if self._period=='d':
                    last = bi
                    for i in range(bi,ei):
                        if self._date[i][0].weekday()==0:
                            xticks.append(i)
                            last = i
                    if last != ei-1:
                        xticks.append(ei-1)
                else:
                    for i in range(bi,ei):
                        if i>0 and self._date[i][0].month!=self._date[i-1][0].month:
                            xticks.append(i)
                if self._trendHeadPos>=0 and self._trendHeadPos<len(self._k):
                    xticks.append(self._trendHeadPos)
                    xticks.append(self._trendHeadPos)
                xticks = np.array(xticks)             
            else:
                xticks = np.arange(bi,ei,10)
        else:
            xticks = []
            for i in range(bi,ei):
                if i>0 and i<len(self._date):
                    if self._date[i][0].day!=self._date[i-1][0].day:
                        xticks.append(i-1)

            if self._trendHeadPos>=0 and self._trendHeadPos<len(self._k):
                xticks.append(self._trendHeadPos)
                xticks.append(self._trendHeadPos)                            
            xticks = np.array(xticks)    
            """  
            if int(self._period) == 15:
                xticks = np.arange(bi,ei,16)
            elif int(self._period) == 5:
                xticks = np.arange(bi,ei,48)
            elif int(self._period) == 60:
                xticks = np.arange(bi,ei,4)
            """
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
                    if v<0:
                        v = len(self._k)+v
                    if v>=bi and v<=ei:
                        plotVline(axs,v,lines['color'] if 'color' in lines else 'blue',
                        linewidth=lines['linewidth'] if 'linewidth' in lines else 1,
                        linestyle=lines['linestyle'] if 'linestyle' in lines else '-',)
        #绘制能量线
        if self._showenergy:
            axs[self._energyInx].plot(x,self._volumeenergy[bi:ei],color='red',linewidth=2)
            axs[self._energyInx].plot(x,self._volumekdj[bi:ei],color='blue',linewidth=1,linestyle='-.')
            axs[self._energyInx].axhline(0,color='green',linestyle='-.')
            axs[self._energyInx].axhline(100,color='red',linestyle='-.')
            if self._szclose is not None:
                axs[self._energyInx].plot(x,self._szvolumeenergy[bi:ei],color='black',linewidth=2,linestyle='--')
                axs[self._energyInx].plot(x,self._szvolumekdj[bi:ei],color='gray',linewidth=1,linestyle='-.')
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
            ct = {5:"orange",10:"pink",20:"cornflowerblue",30:"salmon",60:"violet",242:"lime"}
            for m in self._config['ma']:
                xx,alv = stock.maRangeK(self._k,m,bi,ei)
                if m in ct:
                    axsK.plot(xx,alv,label="MA"+str(m),color=ct[m])
                else:
                    axsK.plot(xx,alv,label="MA"+str(m))
            if len(self._config['ma'])>1:
                axsK.legend()
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
                    axsK.plot([x0,x1],[k*x0+b,k*x1+b],color='orangered' if k>0 else 'royalblue',linewidth=3,linestyle='-.')
            """
            for line in self._trend2:
                if line[1]>bi and line[0]<ei:
                    x0 = line[0]
                    x1 = line[1]
                    k = line[2]
                    b = line[3]
                    axsK.plot([x0,x1],[k*x0+b,k*x1+b],color='orangered' if k>0 else 'royalblue',alpha=0.8,linewidth=6,linestyle='-.')
            """
        if self._trendHeadPos>=0 and self._trendHeadPos<=len(self._k):
            axsK.axvline(self._trendHeadPos,color="red",linewidth=2,linestyle='--')
            for i in range(self._axsInx+1):
                axs[i].axvline(self._trendHeadPos,color="red",linewidth=2,linestyle='--')

        if self._company is not None:
            if self._period=='w':
                p = '周线'
            elif self._period=='d':
                p = '日线'
            else:
                p = '%d分钟线'%(self._period)
            axsK.set_title('%s %s %s'%(self._company[2],self._company[1],p))
        #绘制k线图
        plotK(axsK,self._k,bi,ei)
        #将大盘数据绘制在K线图上
        if self._szclose is not None:
            kmax = self._k[bi:ei,1:4].max()
            kmin = self._k[bi:ei,1:4].min()  
            szkmax = self._szclose[bi:ei].max()
            szkmin = self._szclose[bi:ei].min()
            axsK.plot(x,(self._szclose[bi:ei]-szkmin)*(kmax-kmin)/(szkmax-szkmin)+kmin,color='black',linewidth=2,linestyle='--')
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
            axs[self._macdInx].plot(x,self._macd[bi:ei],label="MACD",color='blue',linewidth=2)
            axs[self._macdInx].axhline(color='black')
            if self._szclose is not None: #绘制大盘macd
                kmax = self._macd[bi:ei].max()
                kmin = self._macd[bi:ei].min()                  
                szkmax = self._szmacd[bi:ei].max()
                szkmin = self._szmacd[bi:ei].min()
                axs[self._macdInx].plot(x,self._szmacd[bi:ei]*(kmax-kmin)/(szkmax-szkmin),color='black',linestyle='--')
                
        #绘制kdj
        if self._showkdj:
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,0],label="K",color='orange')
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,1],label="D",color='blue')
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,2],label="J",color='purple')
        #绘制额外的图表
        if self._showfigure:
            i = 0
            if type(self._config['figure'])==dict:
                figures = self._config['figure']
            elif callable(self._config['figure']):
                figures = self._config['figure'](self)
            for f in figures:
                axsinx = self._figureInx[i]
                for p in f:
                    if 'data' in p:
                        axs[axsinx].plot(x,p['data'][bi:ei],
                        label=p['name'] if 'name' in p else '',
                        color=p['color'] if 'color' in p else 'blue',
                        linewidth=p['linewidth'] if 'linewidth' in p else 1,
                        linestyle=p['linestyle'] if 'linestyle' in p else '-'
                        )
                        if 'hline' in p:
                            axs[axsinx].axhline(p['hline']['y'] if 'y' in p['hline'] else 0,
                            color= p['hline']['color'] if 'color' in p['hline'] else 'black',
                            linewidth=p['hline']['linewidth'] if 'linewidth' in p['hline'] else 1,
                            linestyle=p['hline']['linestyle'] if 'linestyle' in p['hline'] else '-'
                            )
                i+=1
        #一个从外部进行调整图表的手段
        if 'cb' in self._config:
            self._config['cb'](self,axs,bi,ei)
        fig.autofmt_xdate()

        #单独做一个显示层级
        if not self._isupdate:
            self._output = widgets.Output()
            display(self._output)
            self._isupdate = True
        self._output.clear_output(wait=True)
        with self._output:
            plt.show()
        #plt.show()
        """
        这里定制plt.show函数，参加backend_inline.py
        plt.show()调用backend_inline.show
        这里加入命名的display,这保证每次都更新相同的cell
        """
        #if self._isupdate:
        #    plt_show(display_id=self._display_id,isupdate=True)
        #else:
        #    plt_show(display_id=self._display_id,isupdate=False)
        #    self._isupdate = True

    #code2另一只股票，进行比较显示
    def show(self,bi=None,ei=None,code2=None,figsize=(30,14)):
        if bi is None:
            bi = len(self._k)-self._showcount
            if bi<0:
                bi = 0
        if ei is None:
            ei = len(self._k)
        if code2 is not None:
            figsize = (30,8)
            figure2 = Plote(code2,self._period)
        else:
            figure2 = None
        nextbutton = widgets.Button(description="下一页",layout=Layout(width='96px'))
        prevbutton = widgets.Button(description="上一页",layout=Layout(width='96px'))
        zoominbutton = widgets.Button(description="+",layout=Layout(width='48px'))
        zoomoutbutton = widgets.Button(description="-",layout=Layout(width='48px'))
        
        if self._showtrend:
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

        if self._showfigure:
            figuretoggle = widgets.ToggleButton(
                value=self._showfigure,
                description='FIGURE',
                disabled=False,
                button_style='',
                tooltip='FIGURE',
                icon='check')

        mainDropdown = widgets.Dropdown(
            options=['BOLL+','MA','BOLL','TREND','CLEAR'],
            value='TREND',
            description='',
            disabled=False,
            layout=Layout(width='96px')
        )    
        indexDropdown = widgets.Dropdown(
            options=['MACD+','KDJ+','MACD+Best','MACD+BollWidth','CLEAR'],
            value='MACD+',
            description='',
            disabled=False,
            layout=Layout(width='96px')
        )            
        periodDropdown = widgets.Dropdown(
            options=['日线', '周线', '15分钟','5分钟','15分钟校','5分钟校'],
            value='日线',
            description='',
            disabled=False,
            layout=Layout(width='96px')
        )
        refreshbutton = widgets.Button(description="刷新",layout=Layout(width='96px'))                           
        #output = widgets.Output()

        box_layout = Layout(display='flex',
                            flex_flow='wrap',
                            align_items='stretch',
                            border='solid',
                            width='100%')
        stockcode = self._comarg if self._comarg[2]!=':' else self._comarg[0:2]+self._comarg[3:]
        link = widgets.HTML(value="""<a href="https://xueqiu.com/S/%s" target="_blank" rel="noopener">%s</a>"""%(stockcode,stockcode))
        if self._showtrend:
            items = [prevbutton,nextbutton,zoominbutton,zoomoutbutton,backbutton,slider,frontbutton,mainDropdown,indexDropdown,periodDropdown,refreshbutton,link]
        else:
            items = [prevbutton,nextbutton,zoominbutton,zoomoutbutton,mainDropdown,indexDropdown,periodDropdown,refreshbutton,link]
        if self._showfigure:
            items.append(figuretoggle)
        box = Box(children=items, layout=box_layout)
        
        beginPT = bi
        endPT = ei
        showRange = ei-bi            
        needUpdateSlider = True
        def showline():
            nonlocal needUpdateSlider
            self.showKline(beginPT,endPT,figsize=figsize)
            if figure2 is not None:
                bi = figure2.date2index( self.index2date(beginPT) )
                ei = figure2.date2index( self.index2date(endPT) )
                if bi != ei:
                    figure2.showKline(bi,ei,figsize=figsize)
            needUpdateSlider = True

        def setSlider(minv,maxv,value):
            nonlocal needUpdateSlider
            needUpdateSlider = False
            if minv>slider.max:
                slider.max = maxv
                slider.min = minv
            else:
                slider.min = minv
                slider.max = maxv
            slider.value = value

        def on_nextbutton_clicked(b):
            nonlocal beginPT,endPT,showRange
            beginPT += showRange
            endPT += showRange
            
            if endPT >= len(self._k):
                endPT = len(self._k)
                beginPT = endPT-showRange
            if self._showtrend:
                self._trendHeadPos = endPT
                setSlider(beginPT,endPT,endPT)
            showline()
        
        def on_prevbutton_clicked(b):
            nonlocal beginPT,endPT,showRange
            beginPT -= showRange
            endPT -= showRange

            if beginPT < 0 :
                endPT = showRange
                beginPT = 0

            if self._showtrend:
                self._trendHeadPos = endPT
                setSlider(beginPT,endPT,endPT)
            showline()

        def on_zoomin(b):
            nonlocal beginPT,endPT,showRange
            showRange = math.floor(showRange/2)
            beginPT = endPT - showRange
            if self._showtrend:
                self._trendHeadPos = endPT
                setSlider(beginPT,endPT,endPT)
            showline()

        def on_zoomout(b):
            nonlocal beginPT,endPT,showRange
            showRange *= 2
            beginPT = endPT - showRange
            if beginPT < 0:
                beginPT = 0
                endPT = beginPT+showRange
            if self._showtrend:
                self._trendHeadPos = endPT
                setSlider(beginPT,endPT,endPT)
              
            showline()

        def on_change(event):
            source = event['owner']
            if event['new']:
                self.enable(source.description.lower())
            else:
                self.disable(source.description.lower())
            showline()

        def on_sliderChange(event):
            nonlocal needUpdateSlider
            self._trendHeadPos = event['new']
            updateTrend()
            if needUpdateSlider:
                showline()

        def updateTrend():
            self._trend = trend.macdTrend(self._k[:self._trendHeadPos,:],self._macd[:self._trendHeadPos])
            #self._trend2 = trend.large(self._k[:self._trendHeadPos,:],self._trend,0.15)

        def on_prev(b):
            nonlocal needUpdateSlider,beginPT,endPT
            self._trendHeadPos -= 1
            if self._trendHeadPos<0:
                self._trendHeadPos = 0
            needUpdateSlider = False
            if self._trendHeadPos<beginPT-1:#向前移动移动视口
                beginPT = self._trendHeadPos-math.floor(self._showcount/2)
                if beginPT<0:
                    beginPT = 0
                endPT = beginPT+self._showcount
                if endPT>len(self._k):
                    endPT = len(self._k)
                setSlider(beginPT,endPT,self._trendHeadPos)
            
            slider.value = self._trendHeadPos
            updateTrend()
            showline()
            
        def on_next(b):
            nonlocal needUpdateSlider,beginPT,endPT
            self._trendHeadPos += 1
            needUpdateSlider = False
            if self._trendHeadPos>len(self._k):
                self._trendHeadPos = len(self._k)
            if self._trendHeadPos>endPT+1:#向后移动移动视口
                endPT = self._trendHeadPos+math.floor(self._showcount/2)
                if endPT>len(self._k):
                    endPT = len(self._k)
                beginPT = endPT-self._showcount
                if beginPT<0:
                    beginPT=0
                setSlider(beginPT,endPT,self._trendHeadPos)
            slider.value = self._trendHeadPos
            updateTrend()
            showline()

        nextbutton.on_click(on_nextbutton_clicked)
        prevbutton.on_click(on_prevbutton_clicked)

        zoominbutton.on_click(on_zoomin)
        zoomoutbutton.on_click(on_zoomout)

        def on_index(e):
            sel = e['new']
            if sel=='MACD+':
                self.enable('macd')
                self.enable('energy')
                self.disable('kdj')
                self.disable('best')
                self.disable('bollwidth')
            elif sel=='KDJ+':
                self.disable('macd')
                self.enable('energy')
                self.enable('kdj')
                self.disable('best')
                self.disable('bollwidth')
            elif sel=='MACD+Best':
                self.enable('macd')
                self.enable('energy')
                self.disable('kdj')
                self.enable('best')
                self.disable('bollwidth')
            elif sel=='MACD+BollWidth':
                self.enable('macd')
                self.enable('energy')
                self.disable('kdj')
                self.disable('best')
                self.enable('bollwidth')
            elif sel=='CLEAR':
                self.disable('macd')
                self.disable('energy')
                self.disable('kdj')
                self.disable('best')
                self.disable('bollwidth')
            self.config()
            showline()            
        indexDropdown.observe(on_index,names='value')

        def on_main(e):
            sel = e['new']
            if sel=='BOLL+':
                self.enable('boll')
                self.enable('trend')
                self.disable('ma')
            elif sel=='MA':
                self.enable('ma')
                self.disable('boll')
                self.disable('trend')
                self._config['ma'] = [5,10,20,30,60]
            elif sel=='BOLL':
                self.enable('boll')
                self.disable('trend')
                self.disable('ma')
            elif sel=='TREND':
                self.disable('boll')
                self.enable('trend')
                self.enable('ma')
                self._config['ma'] = [20]
            elif sel=='CLEAR':
                self.disable('boll')
                self.disable('trend')
                self.disable('ma')
            self.config()
            showline()

        mainDropdown.observe(on_main,names='value')

        def recalcRange():
            nonlocal beginPT,endPT
            endPT = len(self._k)
            beginPT = len(self._k)-self._showcount
            if beginPT<0:
                beginPT = 0   
            self._trendHeadPos = endPT-1
            setSlider(beginPT,endPT,self._trendHeadPos)

        def on_period(e):
            name2peroid = {
                '日线':['d',False],
                '周线':['w',False],
                '15分钟':[15,False],
                '5分钟':[5,False],
                '15分钟校':[15,True],
                '5分钟校':[5,True]
            }
            period = e['new']
            sel = name2peroid[period]
            self._period = sel[0]
            self._correcttionVolume = sel[1]
            self.reload()
            self.config()
            recalcRange()
            showline()

        periodDropdown.observe(on_period,names='value')

        def refresh(b):
            self.reload(all=False)
            recalcRange()
            showline()
            refreshbutton.button_style = ''
        refreshbutton.on_click(refresh)
        if self._showtrend:
            backbutton.on_click(on_prev)
            frontbutton.on_click(on_next)
            slider.observe(on_sliderChange,names='value')
            
        if self._showfigure:
            figuretoggle.observe(on_change,names='value')

        display(box)
        
        self.showKline(beginPT,endPT,figsize=figsize)
        if figure2 is not None:
            bi = figure2.date2index( self.index2date(beginPT) )
            ei = figure2.date2index( self.index2date(endPT) )
            if bi != ei:
                figure2.showKline(bi,ei,figsize=figsize)

        def updatek15():
            if xueqiu.isTransTime():
                refreshbutton.button_style = 'success' #green button
                #self.reload(all=False)
                #showline()
                self._timer = xueqiu.Timer(xueqiu.nextdt15()+1,updatek15)
            else:
                self._timer = None

        self._timer = xueqiu.Timer(xueqiu.nextdt15()+1,updatek15)
