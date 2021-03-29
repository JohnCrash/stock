from . import stock
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import Formatter
import math
import ipywidgets as widgets
from IPython.display import display,update_display,clear_output
from ipykernel.jsonutil import json_clean,encode_images
from IPython.core.interactiveshell import InteractiveShell
from ipywidgets import Layout, Button, Box
from datetime import date,datetime,timedelta
import time
import copy
from . import trend
import  warnings
from . import shared
from . import xueqiu
import uuid
from . import mylog
#定制show
from matplotlib._pylab_helpers import Gcf
from ipykernel.pylab.backend_inline import _fetch_figure_metadata,show

log = mylog.init('kline.log',name='kline')
warnings.filterwarnings("ignore", module="matplotlib")

_cacheK = {}

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

def output_show(output):
    try:
        for figure_manager in Gcf.get_all_fig_managers():
            format = InteractiveShell.instance().display_formatter.format
            format_dict, md_dict = format(figure_manager.canvas.figure)  
            output.outputs = ({
                'output_type': 'display_data',
                'data':json_clean(encode_images(format_dict)),
                'metadata': {'needs_background': 'light'}
            },)
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
        axs.vlines(i,k[i,3],k[i,2],color=c,zorder=0,linewidth=2)
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

class MyFormatterRT(Formatter):
    def __init__(self, dates,fmt='d h:m:s'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0 or math.ceil(x)!=math.floor(x):
            return ''

        t = self.dates[ind][0]
        if self.fmt=='d h:m:s':
            return '%d %02d:%02d:%02d'%(t.day,t.hour,t.minute,t.second)
        elif self.fmt=='d h:m':
            return '%d %02d:%02d'%(t.day,t.hour,t.minute)
        elif self.fmt=='h:m:s':
            return '%02d:%02d:%02d'%(t.hour,t.minute,t.second)
        elif self.fmt=='h:m':
            return '%02d:%02d'%(t.hour,t.minute)
        else:
            return '%d %02d:%02d'%(t.day,t.hour,t.minute)

class MyFormatterK5(Formatter):
    def __init__(self,times,fmt='%m:%s'):
        self.fmt = fmt
        self._times = times
        self.k5d = ((9,35),(9,40),(9,45),(9,50),(9,55),(10,0),(10,5),(10,10),(10,15),(10,20),(10,25),(10,30),
                    (10,35),(10,40),(10,45),(10,50),(10,55),(11,00),(11,5),(11,10),(11,15),(11,20),(11,25),(11,30),
                    (13,5),(13,10),(13,15),(13,20),(13,25),(13,30),(13,35),(13,40),(13,45),(13,50),(13,55),(14,00),
                    (14,5),(14,10),(14,15),(14,20),(14,25),(14,30),(14,35),(14,40),(14,45),(14,50),(14,55),(15,00))

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        x = int(x)
        if x>=0 and x<len(self._times):
            t = self._times[x][0]
            return "%d:%02d"%(t.hour,t.minute)
        elif x>=len(self._times):
            t = self._times[-1][0]
            offset = x-len(self._times)
            for i in range(len(self.k5d)):
                d = self.k5d[i]
                if t.hour==d[0] and t.minute==d[1]:
                    t = self.k5d[(i+offset+1)%len(self.k5d)]
                    return "%d:%02d"%(t[0],t[1])
        return ''

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

"""
对编码进行映射，因为对于east的资金流向分类代码和雪球的不一样。
"""
def mapxueqiu2east(code):
    m2e = {
        "SH000001":"zjlx/zs000001",
        "SZ399001":'zjlx/zs399001',
        "SZ399006":'zjlx/zs399006',
        "BK0057":"bkzj/BK0473",
        "BK0055":"bkzj/BK0475",
        "BK0056":"bkzj/BK0474",
        "BK0033":"bkzj/BK0438",
        "BK0040":"bkzj/BK0465",
        "BK0044":"bkzj/BK0727",
        "BK0031":"bkzj/BK0456",

        "BK0021":"bkzj/BK0459", #电子元件
        "BK0489":"bkzj/BK0459",

        "BK0444":"bkzj/BK0447", #电子信息
        "BK0063":"bkzj/BK0447",
        "BK0414":"bkzj/BK0447",

        "BK0066":"bkzj/BK0490"
    }
    if code.upper() in m2e:
        return True,m2e[code.upper()]
    else:
        return False,code
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
    disabledate:True #关闭日期
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
    prediction:[[date,volume,open,high,low,close],...]#提前加入未来的预测k线图
    search: function(self) 返回满足条件的索引数组
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
        self._showrsi = False
        self._showvolume = False
        self._showboll = False
        self._showvlines = False
        self._showbest = False
        self._showfigure = False
        self._showbollwidth = False
        self._showtrend = False
        self._showenergy = False
        self._mad = None
        self._rsi = None
        self._showflow = False
        self._currentflow = None
        self._gotoTrendHeandPos = False
        self._show5bigma20 = False
        self._showeps = False #显示macd背离
        self._widths = [1]
        self._heights = [3]        
        self._day_last_line = None
        if len(self._k)==0: #完全没有数据
            return

        if 'ma' in self._config:
            self._showma = True
        if 'eps' in self._config:
            self._showeps = True
        while 'figure' in self._config:
            self._figureInx = []
            if type(self._config['figure'])==list:
                figures = self._config['figure']
            elif callable(self._config['figure']):
                figures = self._config['figure'](self)
            else:
                break
            if figures is not None:
                for f in figures:
                    self._figureInx.append(self._axsInx+1)
                    self._axsInx += 1
                self._showfigure = True
            break
        if 'boll' in self._config:
            self._boll = stock.bollLineK(self._k,self._config['boll'])
            self._showboll = True
            if 'bigma20' in self._config:
                self._show5bigma20 = True
        if 'trend' in self._config and self._config['trend']:
            self._macd,self._dif,self._dea = stock.macd(self._k)
            self._trend,last_line,b = trend.macdTrend(self._k,self._macd)
            #如果是日线的趋势线将被保存,用于小级别中绘制
            if self._period == 'd':
                self._day_trend = self._trend
                self._day_date = self._date
                self._day_last_line = last_line
                self._day_b = b
            #self._trend2 = trend.large(self._k,self._trend,0.15)
            self._showtrend = True
        
        if self._date and 'markpos' in self._config:
            dd = self._config['markpos']
            if type(self._date[-1][0])!=type(dd):
                if type(dd)==str and type(self._date[-1][0])==date:
                    dd = date.fromisoformat(dd)
                elif type(dd)==str and type(self._date[-1][0])==datetime:
                    dd = datetime.fromisoformat(dd)
                elif type(dd)==date and type(self._date[-1][0])==datetime:
                    dd = datetime(dd.year,dd.month,dd.day)
                elif type(dd)==datetime and type(self._date[-1][0])==date:
                    dd = date(dd.year,dd.month,dd.day)
            self._trendHeadPos = len(self._k)-1
            for i in range(len(self._date)):
                if self._date[i][0] == dd:
                    self._trendHeadPos = i
                    self._gotoTrendHeandPos = True
                    break
        else:
            self._trendHeadPos = len(self._k)

        if 'energy' in self._config and self._config['energy']:
            self._energyInx = self._axsInx+1
            self._axsInx += 1
            if self._correcttionVolume and (self._period==5 or self._period==15 or self._period==30 or self._period==60 or self._period==120 or self._period==1):
                volume,mad = stock.correctionVolume(self._k,self._date,self._period)
                self._volumeenergy = stock.kdj(stock.volumeEnergy(volume))[:,2]
                self._volumekdj = stock.kdj(volume)[:,2]
                self._k = np.array(self._k,copy=True)
                self._k[:,0] = volume
            else:
                self._volumeenergy = stock.kdj(stock.volumeEnergyK(self._k))[:,2]
                self._volumekdj = stock.kdj(self._k[:,0])[:,2]
            self._rsi = stock.rsi(self._k[:,4],6)
            self._showenergy = True
        else:
            if self._period==5 or self._period==15:
                volume,mad = stock.correctionVolume(self._k,self._date,self._period)
                if False and self._correcttionVolume:
                    self._k = np.array(self._k,copy=True)
                    self._k[:,0] = volume
                else:
                    self._mad = mad.reshape(-1)
        if 'bollwidth' in self._config and self._config['bollwidth']:
            self._bollwidthInx = self._axsInx+1
            self._axsInx += 1
            self._showbollwidth = True
            if not self._showboll:
                self._boll = stock.bollLineK(self._k)
            self._bollwidth = stock.bollWidth(self._boll)

        if 'macd' in self._config and self._config['macd']:
            self._macdInx = self._axsInx+1
            self._axsInx += 1
            #防止计算两边macd
            if not self._showtrend:
                self._macd,self._dif,self._dea = stock.macd(self._k)
            self._showmacd = True
        if 'kdj' in self._config and self._config['kdj'] is not None:
            self._kdjInx = self._axsInx+1
            self._axsInx += 1
            if type(self._config['kdj'])==int:
                self._kdj = stock.kdjK(self._k,self._config['kdj'])
            elif type(self._config['kdj'])==np.ndarray:
                self._kdj = self._config['kdj']
            self._showkdj = True
        if 'rsi' in self._config and self._config['rsi']:
            self._rsiInx = self._axsInx+1
            self._axsInx += 1
            if self._rsi is None:
                self._rsi = stock.rsi(self._k[:,4],6)
            self._showrsi = True   
        if 'flow' in self._config and self._config['flow']:
            self._flowInx =self._axsInx+1
            self._axsInx += 1
            self._flow = self.getFlow(self._date)
            self._showflow = True                     
        if 'volume' in self._config and self._config['volume']:
            self._volInx =self._axsInx+1
            self._axsInx += 1
            self._volumema20 = stock.ma(self._k[:,0],20)
            self._volumema5 = stock.ma(self._k[:,0],5)
            self._showvolume = True

        #将大盘指数的收盘价显示在图表中
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
                    self._macd,self._dif,self._dea = stock.macd(self._k)
                self._minpt,self._maxpt,_ = stock.MacdBestPt(self._k,self._macd)
            self._showbest = True
        self._keyindex = None
        if 'search' in self._config:
            searchfunc = self._config['search']
            if callable(searchfunc):
                self._keyindex = searchfunc(self)

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
        global _cacheK
        if len(code)>3 and code[2]==':':
            code = code.replace(':','')
        if not (code in _cacheK and period in _cacheK[code]):    
            if period == 'w':
                after = None #全部数据
            elif period == 'd':
                after = stock.dateString(date.today()-timedelta(days=5*365 if self._lastday is None else self._lastday)) #5年数据
            else:
                after = stock.dateString(date.today()-timedelta(days=240 if self._lastday is None else self._lastday))
            
            if period==5 or period=='d':
                c,k,d = stock.loadKline(code,period,after=after)
            elif period=='w':
                c,k,d = stock.loadKline(code,'d',after=after)
            else:
                c,k,d = stock.loadKline(code,5,after=after)
                k,d = stock.mergeK(k,d,period/5)
            
            if code is not _cacheK:
                _cacheK[code] = {}
            _cacheK[code][period] = (c,k,d,after)
        cur = _cacheK[code][period]
        _,k,d = xueqiu.appendK(code,period,cur[1],cur[2])
        return cur[0],k,d
    """
    取得某一天的flow数据
    返回值:([(larg,big,mid,tiny),..],[date,..])
    """
    def getCurrentFlow(self):
        if self._trendHeadPos<=len(self._date) and self._trendHeadPos>0:
            if self._trendHeadPos==len(self._date):
                d = self._date[self._trendHeadPos-1]
            else:
                d = self._date[self._trendHeadPos]
            
            flowk,flowd = xueqiu.getFlow(self.code(),self._lastday)
            flow = ([],[])
            for i in range(len(flowd)):
                if flowd[i][0].year==d[0].year and flowd[i][0].month==d[0].month and flowd[i][0].day==d[0].day:
                    flow[0].append(flowk[i])
                    flow[1].append(flowd[i])
            return flow
        return None
    """
    取得资金流 ,d是k线图日期数组
    """
    def getFlow(self,d):
        flowk,flowd = xueqiu.getFlow(self.code(),self._lastday)
        flow = (flowk,flowd)
        J = 0
        k = np.zeros((len(d),4))
        b = False
        if type(d[0][0])==datetime:
            b = True
        for i in range(len(d)):
            t = d[i][0]
            if not b:
                t = datetime(t.year,t.month,t.day,15,0,0)
            for j in range(J,len(flow[1])):
                t2 = flow[1][j][0]
                if t<t2:
                    k[i] = flow[0][j-1] if j-1>=0 else flow[0][j]
                    break
                elif t==t2:
                    k[i] = flow[0][j]
                    break
            if j == len(flow[1])-1:
                k[i] = flow[0][-1]
            J = j
        return k

    def init(self,company,period,config,date_ = None,companyInfo=None):
        self._period = period
        b,self._showcount = shared.fromRedis('kline.zoom%s'%self._period)
        if not b:
            self._showcount = 80
        if self._period=='d' or self._period=='w':
            if self._mode=='runtime' or (self._mode=='auto' and self.isWatchTime()):
                self._showcount = 80
        
        if type(company)==np.ndarray:
            self._k = company
            self._company = companyInfo
            self._comarg = companyInfo[1] #code
            self._date = date_
        elif type(company)==str:
            self._rate = None
            self._maxrate = None
            self._minrate = None            
            if self._period == 'w': #周线
                self._company,k,d = self.getKlineData(company,'d')
                self._k,self._date = stock.weekK(k,d)
            else:
                self._company,self._k,self._date = self.getKlineData(company,self._period)
                k = self._k
                d = self._date
                #这里计算相对于昨天的涨跌率
                if period=='d':
                    if len(k)>2:
                        self._rate = round((k[-1][4]/k[-2][4]-1)*100,2)
                    else:
                        self._rate = 0
                elif period==15 or period==5:
                    dd = d[-1][0]
                    self._maxk = k[-1][2]
                    self._maxx = len(k)-1
                    self._mink = k[-1][3]
                    self._minx = len(k)-1
                    for i in range(len(d)-2,-1,-1):
                        if d[i][0].day!=dd.day:
                            yk = k[i]
                            self._todaybi = i
                            self._rate = round((k[-1][4]/yk[4]-1)*100,2)
                            self._maxrate = round((self._maxk/yk[4]-1)*100,2)
                            self._minrate = round((self._mink/yk[4]-1)*100,2)
                            break
                        else:
                            if self._maxk < k[i][2]:
                                self._maxk = k[i][2]
                                self._maxx = i
                            if self._mink > k[i][3]:
                                self._mink = k[i][3]
                                self._minx = i
                if 'prediction' in self._configarg:
                    for k_ in self._configarg['prediction']:
                        self._k = np.vstack((self._k,k_[1:]))
                        self._date.append((date.fromisoformat(k_[0]),))
        if len(self._k)==0: #完全没有数据不进行进一步处理
            return
        #将大盘指数画在图表中   
        if "index" in config and config["index"] and self._company[1] != 'SZ399001' and self._company[1] != 'SH000001' and self._company[1] != 'SZ399006':
            #这里做日期对齐
            idxcode = 'SZ399001' if (self._comarg[1]).upper()=='Z' else 'SH000001'
            if self._period=='w':
                _,szk,szd = self.getKlineData(idxcode,'d')
                K = stock.alignK(self._date,szk,szd)
                WK,WD = stock.weekK(K,self._date)
                self._szclose = WK[:,4]
                self._szvolumekdj = stock.kdj(WK[:,0])[:,2]
                self._szvolumeenergy = stock.kdj(stock.volumeEnergyK(WK))[:,2]
                self._szmacd,self._szdif,self._szdea = stock.macd(WK)
            else:
                _,szk,szd = self.getKlineData(idxcode,self._period)
                K = stock.alignK(self._date,szk,szd)
                self._szclose = K[:,4]
                self._szvolumekdj = stock.kdj(K[:,0])[:,2]
                self._szvolumeenergy = stock.kdj(stock.volumeEnergyK(K))[:,2]
                self._szmacd,self._szdif,self._szdea = stock.macd(K)
        else:
            self._szclose = None

    #重新加载对象数据all=True加载全部数据,all=False更新数据
    def reload(self,all=True):
        self.init(self._comarg,self._period,self._config)
        self.config()
    
    def __del__(self):
        if self._timer is not None:
            #self._timer.cancel()
            xueqiu.cancelTimeout(self._timer)

    #company可以是kline数据，可以是code，也可以是公司名称
    #mode = 'normal','runtime','auto'
    def __init__(self,company,period=None,config={},date=None,companyInfo=None,prefix=None,context=None,mode='normal',lastday=None,transpos=None):
        self._timer = None
        self._prefix = prefix
        self._context = context
        self._correcttionVolume = False
        b,p = shared.fromRedis('kline.big5')
        if b:
            self._big5mode = p
        else:
            self._big5mode = False
        self._configarg = config
        self._comarg = company
        self._datearg = date
        self._companyInfoarg = companyInfo
        self._display_id = str(uuid.uuid1())
        self._isupdate = False
        self._rate = None
        self._macd = None
        self._flow = None
        self._flowdata = None
        self._mode = mode
        self._day_trend = None
        self._lastday = lastday
        self._transpos = transpos
        ispervsetting = True if period is None else False
        if period is None:
            b,p = shared.fromRedis('kline.period')
            if b:
                period = p
            else:
                period = 'd'
        b1,main_sel = shared.fromRedis('kline.main%s'%period)
        b2,index_sel = shared.fromRedis('kline.index%s'%period)
        if b1 and b2 and ispervsetting:
            if index_sel=='MACD+':
                self._config = {"macd":True,"energy":True,"volume":True}
            elif index_sel=='KDJ+':
                self._config = {"kdj":9,"macd":True,"volume":True}
            elif index_sel=='MACD+Best':
                self._config = {"macd":True,"energy":True,'best':True,"volume":True}
            elif index_sel=='MACD+BollWidth':
                self._config = {"macd":True,"energy":True,'bollwidth':True,"volume":True}
            elif index_sel=='MACD':
                self._config = {"macd":True,"volume":True}
            elif index_sel=='FLOW':
                self._config = {"flow":True,"volume":True}
            elif index_sel=='CLEAR':
                self._config = {"volume":True}

            if main_sel=='BOLL+':
                self._config["boll"] = 20
                self._config['bigma20'] = True
                #self._config['trend'] = True
            elif main_sel=='MA':
                self._config["ma"] = [5,10,20,30,60]
            elif main_sel=='BOLL':
                self._config["boll"] = 20
            elif main_sel=='TREND':
                self._config["trend"] = True
            elif main_sel=='CLEAR':
                self._config["eps"] = True
        else:
            if period=='d':
                self._config = {"macd":True,"energy":True,"volume":True,"trend":True,"ma":[5,10,20,30,60],"debug":False,"volumeprices":True}            
            elif period==15:
                self._config = {"macd":False,"energy":False,"volume":True,"trend":False,"ma":[],"debug":False,"volumeprices":True}
                self._correcttionVolume = True
            elif period==5:
                self._config = {"macd":False,"energy":False,"volume":True,"trend":False,"ma":[],"debug":False,"volumeprices":True}           
                self._correcttionVolume = True
            else:
                self._config = {"macd":True,"energy":True,"volume":True,"trend":True,"ma":[20],"debug":False,"volumeprices":True}       
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
        elif k=='flow':
            self._config['flow'] = True
        elif k=='eps':
            self._config['eps'] = True
        elif k=='bigma20':
            self._config['bigma20'] = True

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

    def code(self):
        code = self._company[1]
        if len(code)>3 and code[2]==':':
            code = code.replace(':','')
        return code.lower()
    def name(self):
        return self._company[2]
    #当前时间,周1~周5 9:00-15:00返回True
    def isWatchTime(self):
        t = datetime.today()
        return t.weekday()>=0 and t.weekday()<5 and t.hour>=8 and t.hour<=15

    #取得选择天的k5
    def getCurrentK5(self):
        pos = self._trendHeadPos
        _,kd,dd = self.getKlineData(self._comarg,self._period)
        while True:
            _,k5,d5 = self.getKlineData(self._comarg,5)
            if pos>=0 and pos<len(dd):
                d_pos = dd[pos][0]
            elif pos>=len(dd):
                return k5,d5
            else:
                break
            for i in range(len(d5)-1,48,-1):
                d = d5[i][0]
                if d_pos.year==d.year and d_pos.month==d.month and d_pos.day==d.day:
                    return k5[:i+1],d5[:i+1]
            #尝试直接到数据库中查找
            for bd in (1,2,3,20):
                _,k5,d5 = stock.loadKline(self._comarg,5,stock.dateString(d_pos-timedelta(days=bd)),stock.dateString(d_pos+timedelta(days=1)))
                if len(k5)>=96:
                    return k5,d5
            break
        return np.array([]).reshape(-1,5),[]

    #显示K线图
    def showKline(self,bi=None,ei=None,figsize=(32,16)):  
        if self._axsInx==0:
            return
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
        axsK = None
        #绘制趋势线
        def drawTrendLine(ax,period,dates,cx0,cx1,cy0=None,cy1=None,lw=3):
            if type(period)==int and self._day_trend is not None and len(self._day_trend)>2:
                def get_date_index(d,t):
                    lsi = -1
                    isb = False
                    for i in range(len(dates)):
                        s = dates[i][0]
                        if s.year==d.year and s.month==d.month and s.day==d.day:
                            if t==0:
                                return i
                            else:
                                lsi = i
                                isb = True
                        elif isb and lsi!=-1:
                            return lsi
                    if isb and lsi!=-1:
                        return lsi
                    elif t==1 and dates[0][0]<datetime(d.year,d.month,d.day):
                        return len(dates)-1
                    else:
                        return 0
                def get_date_by_index(date,i):
                    i = int(i)
                    if i>=len(date):
                        i = len(date)-1
                    return date[i][0]
                def line_crop(x0,x1,y0,y1): #让直线在bi和ei之间，防止这些直线压缩主视图
                    if x1==x0:
                        return False,0,0,0,0
                    k = (y1-y0)/(x1-x0)
                    b = y0-k*x0
                    if x0<cx0:
                        xx0 = cx0
                    elif x0>cx1:
                        xx0 = cx1
                    else:
                        xx0 = x0
                    if x1<cx0:
                        xx1 = cx0
                    elif x1>cx1:
                        xx1 = cx1
                    else:
                        xx1 = x1
                    if xx0==xx1:
                        return False,0,0,0,0
                    if cy0 is not None and cy1 is not None:
                        #对y方向也进行剪切
                        yy0 = k*xx0+b
                        yy1 = k*xx1+b
                        if yy0<cy0:
                            yy0 = cy0
                        elif yy0>cy1:
                            yy0 = cy1
                        if yy1<cy0:
                            yy1 = cy0
                        elif yy1>cy1:
                            yy1 = cy1
                        return yy0!=yy1,(yy0-b)/k,(yy1-b)/k,yy0,yy1
                    else:
                        return True,xx0,xx1,k*xx0+b,k*xx1+b
                for i in [-3,-2,-1]:
                    line = self._day_trend[i]

                    line_x0_date = get_date_by_index(self._day_date,line[0])
                    line_x1_date = get_date_by_index(self._day_date,line[1])
                    x0 = get_date_index(line_x0_date,0)
                    x1 = get_date_index(line_x1_date,1)
                    #print(i,x0,x1,line_x0_date,line_x1_date,len(dates))
                    k = line[2]
                    b = line[3]
                    if i==-2 and self._day_b and x1!=x0: #对趋势线做延长处理 
                        x2 = len(dates)-1
                        y2 = k*(line[1]-line[0])*(x2-x1)/(x1-x0)+k*line[1]+b
                        isv,X0,X1,Y0,Y1 = line_crop(x0,x2,k*line[0]+b,y2)
                        if isv:
                            ax.plot([X0,X1],[Y0,Y1],color='orangered' if k>0 else 'royalblue',linewidth=lw,linestyle='-.')
                    else:
                        isv,X0,X1,Y0,Y1 = line_crop(x0,x1,k*line[0]+b,k*line[1]+b)
                        if isv:
                            ax.plot([X0,X1],[Y0,Y1],color='orangered' if k>0 else 'royalblue',linewidth=lw,linestyle='-.')
                if self._day_last_line is not None:
                    #绘制平均斜率
                    for line in self._day_last_line:
                        line_x0_date = get_date_by_index(self._day_date,line[0])
                        line_x1_date = get_date_by_index(self._day_date,line[1])
                        x0 = get_date_index(line_x0_date,0)
                        x1 = get_date_index(line_x1_date,1)                
                        k = line[2]
                        b = line[3]
                        if self._day_b and x1!=x0:#对趋势线做延长处理 
                            x2 = len(dates)-1
                            y2 = k*(line[1]-line[0])*(x2-x1)/(x1-x0)+k*line[1]+b
                            isv,X0,X1,Y0,Y1 = line_crop(x0,x2,k*line[0]+b,y2)    
                            if isv:
                                ax.plot([X0,X1],[Y0,Y1],color='lightsteelblue' if k<0 else 'lightcoral',linewidth=lw,linestyle='--')
                        else:
                            isv,X0,X1,Y0,Y1 = line_crop(x0,x1,k*line[0]+b,k*line[1]+b)
                            if isv:                
                                ax.plot([X0,X1],[Y0,Y1],color='lightsteelblue' if k<0 else 'lightcoral',linewidth=lw,linestyle='--')                
            else:
                if self._showtrend:
                    for line in self._trend:
                        if (line[1]>=cx0 and line[1]<=cx1) or (line[0]>=cx0 and line[0]<=cx1):
                            x0 = line[0]
                            x1 = line[1]
                            k = line[2]
                            b = line[3]
                            if type(period)==str or self._day_trend is None:
                                ax.plot([x0,x1],[k*x0+b,k*x1+b],color='orangered' if k>0 else 'royalblue',linewidth=lw,linestyle='-.')
                            else:
                                ax.plot([x0,x1],[k*x0+b,k*x1+b],color='orangered' if k>0 else 'royalblue',linewidth=lw,linestyle='-.',alpha=0.6)                
                #绘制平均斜率
                if axsK is not None and self._day_last_line is not None:
                    for line in self._day_last_line:
                        x0 = line[0]
                        x1 = line[1]
                        k = line[2]
                        b = line[3]
                        axsK.plot([x0,x1],[k*x0+b,k*x1+b],color='lightsteelblue' if k<0 else 'lightcoral',linewidth=lw,linestyle='--')

        while True:
            if not (self._period==5 and self._big5mode) and self._mode=='runtime' or (self._mode=='auto' and self.isWatchTime()): #下面的代码在右侧开辟一个区域绘制5分钟时k图
                gs_kw = dict(width_ratios=[2,1], height_ratios=self._heights)
                fig, ax = plt.subplots(self._axsInx+1,2,sharex=True,figsize=figsize,gridspec_kw = gs_kw)
                axs = ax[:,0]
                gs = axs[0].get_gridspec()
                for it in ax[:,1]:
                    it.remove()          
                if self._axsInx<2:
                    axk5 = fig.add_subplot(gs[:-1,-1])
                else:
                    axk5 = fig.add_subplot(gs[:-2,-1])                          
                if not self._showflow:
                    if self._axsInx>=2:
                        axb5 = fig.add_subplot(gs[-2,-1])
                    else:
                        axb5 = None
                    axv5 = fig.add_subplot(gs[-1,-1])
                    axflow = None
                else:#显示资金流入流出
                    if self._axsInx<2:
                        axflow = fig.add_subplot(gs[-1,-1])
                    else:
                        axflow = fig.add_subplot(gs[-2:,-1])
                    axv5 = None
                    axb5 = None
                    flow = self.getCurrentFlow()
                    if flow is not None and len(flow)>0 and len(flow[0])>0:
                        d = np.zeros((len(flow[0]),5))
                        i = 0
                        dd = []
                        xticks=[]
                        for i in range(len(flow[0])):
                            v = flow[0][i]
                            dd.append(flow[1][i])
                            d[i][0] = i
                            d[i][1] = v[0]
                            d[i][2] = v[1]
                            d[i][3] = v[2]
                            d[i][4] = v[3]
                            i+=1     

                        axflow.xaxis.set_major_formatter(MyFormatterRT(flow[1],'h:m'))
                        axflow.plot(d[:,0],d[:,1],color="red",label="巨 %d亿"%(d[-1,1]/1e8))
                        axflow.plot(d[:,0],d[:,2],color="yellow",label="大 %d亿"%(d[-1,2]/1e8))
                        axflow.plot(d[:,0],d[:,3],color="cyan",label="中 %d亿"%(d[-1,3]/1e8))
                        axflow.plot(d[:,0],d[:,4],color="purple",label="小 %d亿"%(d[-1,4]/1e8))
                        #axflow.set_xticks(xticks)
                        axflow.grid(True)
                        axflow.set_xlim(0,60*4)
                        axflow.legend()
                    axflow.axhline(y=0,color='black',linestyle='--')
                k5s,d5s = self.getCurrentK5()
                if len(d5s)>0:
                    axk5.set_title('%s 5分钟K'%(stock.dateString(d5s[-1][0])))
                else:
                    axk5.set_title('5分钟K')
                k5 = k5s[-48*20:]
                d5 = d5s[-48*20:]
                if len(d5)<1:
                    break #确保没有数据的股票不会出错(例如摘牌的)
                
                todayei = len(k5)
                if todayei<1:
                    break
                maxk5close = k5[todayei-1][2]
                maxk5x = todayei-1
                mink5close = k5[todayei-1][3]
                mink5x = todayei-1
                todaybi = 0
                for i in range(todayei-1,-1,-1):
                    if d5[i][0].day != d5[-1][0].day:
                        todaybi = i+1
                        k5yc = k5[i][4]
                        k5currate = round((k5[-1][4]/k5[i][4]-1)*100,2)
                        k5maxrate = round((maxk5close/k5[i][4]-1)*100,2)
                        k5minrate = round((mink5close/k5[i][4]-1)*100,2)
                        break
                    else:
                        if k5[i][2]>maxk5close:
                            maxk5close = k5[i][2]
                            maxk5x = i
                        if k5[i][3]<mink5close:
                            mink5close = k5[i][3]
                            mink5x = i
                tb = np.zeros((len(k5),))
                yb = np.zeros((len(k5),))
                for i in range(todaybi,len(k5)):
                    tb[i] = k5[i,0]+tb[i-1]
                for i in range(todaybi-48,todaybi):
                    yb[i] = k5[i,0]+yb[i-1]
                axk5.set_xlim(todaybi-1,todaybi+48)
                xticks = []
                for i in [0,5,11,17,23,29,35,41,47]:
                    xticks.append(todaybi+i)
                xticks.append(todayei-1)
                xticks.append(todayei-1)
                axk5.set_xticks(xticks)
                axk5.axhline(y=k5yc,color='black',linestyle='--')
                axk5.grid(True)
                if axv5 is not None:
                    axv5.xaxis.set_major_formatter(MyFormatterK5(d5))
                    axv5.set_xlim(todaybi-1,todaybi+48)
                    axv5.set_xticks(xticks)
                    axv5.set_yscale('log')
                    axv5.grid(True)

                k5x = np.linspace(todaybi,todayei-1,todayei-todaybi)
                plotK(axk5,k5,todaybi,todayei)
                #如果不是大盘，将大盘绘制在图表的对应位置
                if self._comarg.lower()!='sz399001' and self._comarg.lower()!='sh000001' and self._comarg.lower()!='sh399006':
                    b,szk,szd = xueqiu.K('SZ399001',5,todayei-todaybi)
                    if b:
                        szkmax = szk[:,4].max()
                        szkmin = szk[:,4].min()
                        if szkmax-szkmin!=0 and k5x.shape[0]==szk.shape[0]:
                            axk5.plot(k5x,(szk[:,4]-szkmin)*(maxk5close-mink5close)/(szkmax-szkmin)+mink5close,color='black',linewidth=2,linestyle='--',label='szk5')
                if maxk5x<todayei-3:
                    axk5.text(maxk5x,maxk5close,str(k5maxrate)+"%",linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='center',verticalalignment='bottom',color='red' if k5maxrate>=0 else 'darkgreen')
                if mink5x<todayei-3:
                    axk5.text(mink5x,mink5close,str(k5minrate)+"%",linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='center',verticalalignment='top',color='red' if k5minrate>=0 else 'darkgreen')
                if k5[todayei-1,4]>k5[todayei-2,4]:
                    k5cury = max(k5[todayei-1,2],k5[todayei-2,2])
                    k5curyb = True
                else:
                    k5cury = min(k5[todayei-1,3],k5[todayei-2,3])
                    k5curyb = False
                axk5.text(todayei-1,k5cury,str(k5currate)+"%",linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='center',verticalalignment='top' if not k5curyb else 'bottom',color='red' if k5currate>=0 else 'darkgreen')
                ck5v,mad = stock.correctionVolume(k5,d5,5)
                #绘制一条均线
                k5ma30 = stock.maK(k5[todaybi:],60)
                axk5.plot(k5x,k5ma30,color='darkorange',linestyle='--')
                if axv5 is not None:
                    axv5.step(k5x,k5[todaybi:todayei,0],label='volume')
                    axv5.step(k5x,mad[-1,-todayei+todaybi:],label='mad',color='orangered')
                    axv5.axhline(color='black')
                if axb5 is not None:
                    axb5.plot(k5x,tb[todaybi:todayei],color='dodgerblue',label='today')
                    axb5.plot(np.linspace(todaybi,todaybi+47,48),yb[todaybi-48:todaybi],color='darkorange',label='yesterday')
                    axb5.set_xticks(xticks)
                    axb5.set_xlim(todaybi-1,todaybi+48)
                    axb5.grid(True)            
                #drawTrendLine(axk5,5,d5,todaybi-1,todaybi+48,k5[todaybi-1:todaybi+48,3].min(),k5[todaybi-1:todaybi+48,2].max(),2)
            else:
                gs_kw = dict(width_ratios=self._widths, height_ratios=self._heights)
                fig, axs = plt.subplots(self._axsInx+1,1,sharex=True,figsize=figsize,gridspec_kw = gs_kw)
            break #while True

        fig.subplots_adjust(hspace=0.02,wspace=0.05) #调整子图上下间距
        axsK = axs if self._axsInx==0 else axs[0]
        if self._date is not None:
            if not('disabledate' in self._config and self._config['disabledate']==True):
                axsK.xaxis.set_major_formatter(MyFormatter(self._date,self._period))
        #时间坐标网格线，天的画在星期一，其他的以天为单位
        xticks = []
        if self._period=='d' or self._period=='w':
            if self._date is not None:
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
                if self._trendHeadPos>=bi and self._trendHeadPos<ei and self._trendHeadPos>=0 and self._trendHeadPos<len(self._k):
                    xticks.append(self._trendHeadPos)
                    xticks.append(self._trendHeadPos)           
            else:
                xticks = np.arange(bi,ei,10)
        else:
            for i in range(bi,ei):
                if i>0 and i<len(self._date):
                    if self._date[i][0].day!=self._date[i-1][0].day:
                        xticks.append(i)
            if self._trendHeadPos>=bi and self._trendHeadPos<ei and self._trendHeadPos>=0 and self._trendHeadPos<len(self._k):
                xticks.append(self._trendHeadPos)
                xticks.append(self._trendHeadPos)  
        x = np.linspace(bi,ei-1,ei-bi)
        #绘制一系列的竖线贯彻整个图例
        if self._showvlines:
            vlines = self._config['vlines']
            for lines in vlines:
                for v in lines['x']:
                    if v<0:
                        v = len(self._k)+v
                    if v>=bi and v<=ei:
                        xticks.append(v)
                        xticks.append(v)
                        plotVline(axs,v,lines['color'] if 'color' in lines else 'blue',
                        linewidth=lines['linewidth'] if 'linewidth' in lines else 1,
                        linestyle=lines['linestyle'] if 'linestyle' in lines else '-',)
        xticks = np.array(xticks) 
        if self._axsInx==0:
            axsK.set_xlim(bi,ei)
            axsK.set_xticks(xticks)
            axsK.grid(True)
        else:
            for i in range(self._axsInx+1):
                axs[i].set_xlim(bi,ei)
                axs[i].set_xticks(xticks)
                axs[i].grid(True)                        
        #绘制能量线
        if self._showenergy:
            axs[self._energyInx].plot(x,self._volumeenergy[bi:ei],color='red',linewidth=2)
            axs[self._energyInx].plot(x,self._volumekdj[bi:ei],color='blue',linewidth=1,linestyle='-.')
            axs[self._energyInx].axhline(0,color='green',linestyle='-.')
            axs[self._energyInx].axhline(100,color='red',linestyle='-.')
            if self._szclose is not None:
                axs[self._energyInx].plot(x,self._szvolumeenergy[bi:ei],color='black',linewidth=2,linestyle='--')
                axs[self._energyInx].plot(x,self._szvolumekdj[bi:ei],color='gray',linewidth=1,linestyle='-.')
            #将rsi指标显示在能量线上,做范围调整，标准rsi<20是超买，>80是超卖，将其调整到0-100
            rsi100 = self._rsi[bi:ei]*1.4-20
            axs[self._energyInx].plot(x,rsi100,label="RSI",color='orange',linestyle='--')
        #绘制bollwidth
        if self._showbollwidth:
            axs[self._bollwidthInx].plot(x,self._bollwidth[bi:ei],color='red',linewidth=2)
            #axs[self._bollwidthInx].axhline(self._config['bollwidth'],color='black') 
            axs[self._bollwidthInx].axhline(0.1,color='green') 
        #绘制macd最佳买卖点
        if self._showbest:
            for v in self._minpt:
                if v>=bi and v<=ei:
                    plotVline(axs,v,'green',linewidth=4,linestyle='-.')
            for v in self._maxpt:
                if v>=bi and v<=ei:
                    plotVline(axs,v,'red',linewidth=4,linestyle='-.')
        """绘制缺口"""
        if self._period=='d':
            gaps = stock.gap(self._k[:self._trendHeadPos+1])            
            for gap in gaps:
                if gap[0]>=bi and gap[1]<=ei:
                    axsK.broken_barh([(gap[0],gap[1]-gap[0])],(gap[2],gap[3]-gap[2]),facecolor='red' if gap[4]>0 else 'green',alpha=0.4)
        """绘制均线"""                
        if self._showma:
            ct = {5:"orange",10:"springgreen",20:"cornflowerblue",30:"salmon",60:"violet",242:"lime"}
            for m in self._config['ma']:
                xx,alv = stock.maRangeK(self._k,m,bi,ei)
                if m in ct:
                    axsK.plot(xx,alv,label="MA"+str(m),color=ct[m])
                else:
                    axsK.plot(xx,alv,label="MA"+str(m))
            if len(self._config['ma'])>1:
                axsK.legend()
        ma1520 = None
        ma3020 = None
        ma6020 = None
        xx = None
        xx2 = None
        """绘制BOLL线"""
        if self._showboll:

            if self._show5bigma20 and self._period==5:
                xx2,ma1520 = stock.maRangeK(self._k,20*3,bi,ei)#15分钟的20均线
                xx2,ma3020 = stock.maRangeK(self._k,20*6,bi,ei) #30分钟的20均线
                xx2,ma6020 = stock.maRangeK(self._k,20*12,bi,ei) #60分钟的20均线,相当于日线的5日均线线
                xx2,mad6080 = stock.maRangeK(self._k,20*12*4,bi,ei) #60分钟的80均线,相当于日线的20日均线线
                axsK.plot(xx2,ma1520,label="K15MA20",linestyle='--',linewidth=3,alpha=0.6,color='lightsteelblue')
                axsK.plot(xx2,ma3020,label="K30MA20",linestyle='--',linewidth=6,alpha=0.6,color='lime')
                axsK.plot(xx2,ma6020,label="K60MA20",linestyle='--',linewidth=12,alpha=0.6,color='magenta')
                axsK.plot(xx2,mad6080,label="K60MA20",linestyle='--',linewidth=24,alpha=0.4,color='orange')
            elif self._show5bigma20 and self._period==15:
                xx2,ma1520 = stock.maRangeK(self._k,20,bi,ei)#15分钟的20均线
                xx2,ma3020 = stock.maRangeK(self._k,20*2,bi,ei) #30分钟的20均线
                xx2,ma6020 = stock.maRangeK(self._k,20*4,bi,ei) #60分钟的20均线,相当于日线的5日均线线
                xx2,mad6080 = stock.maRangeK(self._k,20*4*4,bi,ei) #60分钟的80均线,相当于日线的20日均线线
                axsK.plot(xx2,ma1520,label="K15MA20",linestyle='--',linewidth=3,alpha=0.6,color='lightsteelblue')
                axsK.plot(xx2,ma3020,label="K30MA20",linestyle='--',linewidth=6,alpha=0.6,color='lime')
                axsK.plot(xx2,ma6020,label="K60MA20",linestyle='--',linewidth=12,alpha=0.6,color='magenta')
                axsK.plot(xx2,mad6080,label="K60MA20",linestyle='--',linewidth=24,alpha=0.4,color='orange')
            else:
                axsK.plot(x,self._boll[bi:ei,0],label='low',color='magenta') #low
                axsK.plot(x,self._boll[bi:ei,1],label='mid',color='royalblue') #mid
                axsK.plot(x,self._boll[bi:ei,2],label='upper',color='orange') #upper
        if self._showflow:
            if self._period=='d' or self._period=='w':
                c = self.code()
                if c[2:]=='000001' or c[2:]=='399001':
                    flow = np.zeros((self._flow.shape[0],))
                    for i in range(len(flow)):
                        if i>0:
                            flow[i] = self._flow[i,0]+flow[i-1]
                        else:
                            flow[i] = self._flow[i,0]
                    fkdj = stock.kdj(flow,13)
                    axs[self._flowInx].plot(x,fkdj[bi:ei,0],label='k',linewidth=1,color='orange')
                    axs[self._flowInx].plot(x,fkdj[bi:ei,1],label='d',linewidth=1,color='blue')
                    axs[self._flowInx].plot(x,fkdj[bi:ei,2],label='j',linewidth=1,color='purple')
                else:
                    axs[self._flowInx].plot(x,self._flow[bi:ei,3],label='ting',linewidth=1,color='purple')
                    axs[self._flowInx].plot(x,self._flow[bi:ei,2],label='mid',linewidth=1,color='cyan')
                    axs[self._flowInx].plot(x,self._flow[bi:ei,1],label='big',linewidth=1,color='yellow')
                    axs[self._flowInx].plot(x,self._flow[bi:ei,0],label='larg',linewidth=2,color='red')
            else: #确保相同天是连续的，不同天是断开的
                dss = []
                dds = self._date
                ld = dds[0][0].day
                bii = 0
                for i in range(len(dds)):
                    if dds[i][0].day!=ld:
                        dss.append((bii,i))
                        bii = i
                        ld = dds[i][0].day
                if bii != len(dds)-1:
                    dss.append((bii,len(dds)))
                for ds in dss:
                    bii = ds[0]
                    eii = ds[1]
                    if (bii>=bi and bii<=ei) or (eii>=bi and eii<=ei):
                        xx = np.linspace(bii,eii-1,eii-bii)
                        axs[self._flowInx].plot(xx,self._flow[bii:eii,3],label='ting',linewidth=1,color='purple')
                        axs[self._flowInx].plot(xx,self._flow[bii:eii,2],label='mid',linewidth=1,color='cyan')
                        axs[self._flowInx].plot(xx,self._flow[bii:eii,1],label='big',linewidth=1,color='yellow')
                        axs[self._flowInx].plot(xx,self._flow[bii:eii,0],label='larg',linewidth=2,color='red')
            axs[self._flowInx].axhline(color='black',linestyle='--')

        #绘制趋势线
        if self._showtrend:
            #将日线的趋势线绘制到小级别图表中(仅仅绘制最后2个趋势线)
            drawTrendLine(axsK,self._period,self._date,bi,ei)
        if self._trendHeadPos>=0 and self._trendHeadPos<=len(self._k):
            axsK.axvline(self._trendHeadPos,color="red",linewidth=2,linestyle='--')
            for i in range(1,self._axsInx+1):
                axs[i].axvline(self._trendHeadPos,color="red",linewidth=2,linestyle='--')

        if self._company is not None:
            if self._period=='w':
                p = '周线'
            elif self._period=='d':
                p = '日线'
            else:
                p = '%d分钟线'%(self._period)
            isgame = 'disabledate' in self._config and self._config['disabledate']
            if not isgame:
                if self._prefix is None:
                    if self._context is not None and len(self._context)>0:
                        axsK.set_title('%s %s %s (%s)'%(self._company[2],self._company[1],p,self._context))
                    else:
                        axsK.set_title('%s %s %s'%(self._company[2],self._company[1],p))
                else:
                    if self._context is not None and len(self._context)>0:
                        axsK.set_title('%s%s %s %s (%s)'%(self._prefix,self._company[2],self._company[1],p,self._context))
                    else:
                        axsK.set_title('%s%s %s %s'%(self._prefix,self._company[2],self._company[1],p))
        #绘制k线图
        plotK(axsK,self._k,bi,ei)
        #将大盘数据绘制在K线图上
        if False and self._szclose is not None:
            kmax = self._k[bi:ei,1:4].max()
            kmin = self._k[bi:ei,1:4].min()  
            szkmax = self._szclose[bi:ei].max()
            szkmin = self._szclose[bi:ei].min()
            axsK.plot(x,(self._szclose[bi:ei]-szkmin)*(kmax-kmin)/(szkmax-szkmin)+kmin,color='black',linewidth=2,linestyle='--')
        #绘制成交量
        if self._showvolume:
            if type(self._period)==str:
                #日线周线使用红绿柱
                mp = np.copy(self._k[bi:ei,0])
                mp[self._k[bi:ei,4]<self._k[bi:ei,1]] = 0
                mn = np.copy(self._k[bi:ei,0])
                mn[self._k[bi:ei,4]>self._k[bi:ei,1]] = 0
                axs[self._volInx].bar(x,mp,color='red')
                axs[self._volInx].bar(x,mn,color='green')
                axs[self._volInx].plot(x,self._volumema20[bi:ei],label='vma20',color='orange') #low
                axs[self._volInx].plot(x,self._volumema5[bi:ei],label='vma5',color='cornflowerblue') #low                
            else:
                axs[self._volInx].step(x,self._k[bi:ei,0],where='mid',label='volume')
                if self._mad is not None: #绘制5分钟或者15分钟的碗型
                    axs[self._volInx].step(x,self._mad[bi:ei],where='mid',label='mad',color='orangered') #low
                else:
                    #axs[self._volInx].plot(x,self._k[bi:ei,0],label="volume",alpha=0.6)
                    if type(self._period) == str:
                        axs[self._volInx].plot(x,self._volumema20[bi:ei],label='vma20',color='red') #low
                        axs[self._volInx].plot(x,self._volumema5[bi:ei],label='vma5',color='green') #low
                        #axs[self._volInx].plot(x,self._volumema5[bi:ei],label='vma5',color='yellow') #mid
            axs[self._volInx].axhline(color='black')
        #绘制交易点
        if 'trans' in self._config:
            plotTransPt(axs,self._axsInx,self._config['trans'],bi,ei)
      
        axsK.grid(True)
        #这里显示涨跌比率
        if self._rate is not None and ei==len(self._k):
            if self._k[-1][4]>self._k[-2][4]:
                kcury = max(self._k[-1][2],self._k[-2][2])
                kcurb = True
            else:
                kcury = min(self._k[-1][3],self._k[-2][3])
                kcurb = False
            axsK.text(len(self._k)-1,kcury,str(self._rate)+"%",linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='center',verticalalignment='top' if not kcurb else 'bottom',color='red' if self._rate>=0 else 'darkgreen') #,transform=axsK.transAxes
            if self._maxrate is not None: #绘制今天范围线
                #axsK.hlines(y=self._maxk,xmin=self._todaybi+1,xmax=len(self._k),color='red' if self._maxrate>0 else 'green',linestyle='--') #
                #axsK.hlines(y=self._mink,xmin=self._todaybi+1,xmax=len(self._k),color='red' if self._minrate>0 else 'green',linestyle='--')
                if self._maxx<len(self._k)-3:
                    axsK.text(self._maxx,self._maxk,str(self._maxrate)+"%",linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='center',verticalalignment='bottom',color='red' if self._maxrate>=0 else 'darkgreen')
                if self._minx<len(self._k)-3:
                    axsK.text(self._minx,self._mink,str(self._minrate)+"%",linespacing=13,fontsize=12,fontweight='black',fontfamily='monospace',horizontalalignment='center',verticalalignment='top',color='red' if self._minrate>=0 else 'darkgreen')
        #绘制macd
        if self._showmacd:
            #axs[self._macdInx].plot(x,self._macd[bi:ei],label="MACD",color='blue',linewidth=2)
            if (self._period==5 or self._period==15) and ma6020 is not None:#小级别的直接绘制乖离率
                axs[self._macdInx].plot(xx2,(ma1520-ma6020)/self._k[bi:ei,4],linewidth=4)
                axs[self._macdInx].plot(xx2,(ma1520-ma3020)/self._k[bi:ei,4]) #mid
                axs[self._macdInx].axhline(color='black',linestyle='--')
            else:
                mp = np.copy(self._macd[bi:ei])
                mp[mp<0] = 0
                mn = np.copy(self._macd[bi:ei])
                mn[mn>0] = 0
                axs[self._macdInx].bar(x,mp,color='red')
                axs[self._macdInx].bar(x,mn,color='green')
                axs[self._macdInx].plot(x,self._dif[bi:ei],label="DIF",color='orange',linewidth=2)
                axs[self._macdInx].plot(x,self._dea[bi:ei],label="DEA",color='cornflowerblue',linewidth=2)
                axs[self._macdInx].axhline(color='black')
                if self._szclose is not None: #绘制大盘macd
                    kmax = self._macd[bi:ei].max()
                    kmin = self._macd[bi:ei].min()                  
                    szkmax = self._szmacd[bi:ei].max()
                    szkmin = self._szmacd[bi:ei].min()
                    axs[self._macdInx].plot(x,self._szmacd[bi:ei]*(kmax-kmin)/(szkmax-szkmin),color='black',linestyle='--')
                #macd背离点
                if self._showeps:
                    eps = stock.macdDeviate(self._k[bi:ei,4],self._macd[bi:ei])
                    for i in eps:
                        x = bi+i[1]
                        axs[self._macdInx].annotate('%.1f'%(self._macd[x]),xy=(x,self._macd[x]),xytext=(-40, 50), textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",
                                connectionstyle="angle,angleA=0,angleB=90,rad=10"),fontsize='large',color='red' if i[0]>0 else 'green')
                        x1 = bi+i[2]
                        axs[self._macdInx].annotate('%.1f'%(self._macd[x1]),xy=(x1,self._macd[x1]),xytext=(-40, 50), textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",
                                connectionstyle="angle,angleA=0,angleB=90,rad=10"),fontsize='large',color='red' if i[0]>0 else 'green')
                    eps = stock.extremePoint(self._macd[bi:ei])
                    for i in eps:
                        x = bi+i[0]
                        axs[self._macdInx].annotate('%.1f'%(self._macd[x]),xy=(x,self._macd[x]),xytext=(-30, 30 if i[1]>0 else -30), textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",
                                connectionstyle="angle,angleA=0,angleB=90,rad=10"),fontsize='large')

        #搜索低级别的macd背离
        if self._showeps and self._period=='d':
            k5s,d5s = self.getCurrentK5()
            for p in [15,30,60,120]:
                if p==5:
                    k,d = k5s,d5s
                else:
                    k,d = stock.mergeK(k5s,d5s,p/5)
                eps = stock.macdDeviate(k[:,4])
                for i in eps:
                    t = d[i[2]][0]
                    x1 = self.date2index(date(year=t.year,month=t.month,day=t.day))
                    if x1>=bi and x1<=ei:
                        axsK.annotate('%s'%(p),xy=(x1,self._k[x1,2] if i[0]>0 else self._k[x1,3]),xytext=(-50, 50 if i[0]>0 else -50),
                        textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=90,rad=10"),
                        fontsize='large',color='red' if i[0]>0 else 'green')
        #这里测试均线支撑算法
        if False and (self._period==5 or self._period==15):
            for i in (120,240,480,960):
                if self._period==5:
                    nn = i
                else:
                    nn = int(i/3)
                if i==60 or i==120:
                    mm = nn*2
                elif i==240:
                    mm = nn*4
                else:
                    mm = None              
                r = stock.calcHoldup(self._k,self._date,nn,mm)
                if i==60:
                    c = 'gray'
                    z = 50
                elif i==120:
                    c = 'green'
                    z = -25
                elif i==240:
                    c = 'purple'
                    z = -50
                elif i==480:
                    c = 'blue'
                    z = -75
                else:
                    c = 'orange'
                    z = -100
                for hp in r:
                    high = hp[0]
                    low = hp[1]
                    x1 = hp[2]
                    if x1>bi and x1<=ei:
                        if high>bi:
                            axsK.plot([high,low],[self._k[high,2],self._k[low,3]],color=c,linestyle='--')
                            axsK.plot([low,x1],[self._k[low,2],self._k[x1,3]],color=c,linestyle='--')
                        axsK.annotate('%s+'%(i/4),xy=(x1,self._k[x1,3]),xytext=(-50, z),
                                textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=90,rad=10"),
                                fontsize='large',color=c)                            

        #买卖点数据
        if self._transpos is not None:
            for p in self._transpos:
                x1 = p[2]
                if x1>=bi and x1<=ei:
                    axsK.annotate('%s'%(p[0]),xy=(x1,self._k[x1,4]),xytext=(-50, -50 if p[1]==0 else 50),
                    textcoords='offset points',bbox=dict(boxstyle="round", fc="1.0"),arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=90,rad=10"),
                    fontsize='large',color='red' if p[1]==0 else 'green')
        #绘制kdj
        if self._showkdj:
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,0],label="K",color='orange')
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,1],label="D",color='blue')
            axs[self._kdjInx].plot(x,self._kdj[bi:ei,2],label="J",color='purple')
        #绘制rsi
        if self._showrsi:
            axs[self._rsiInx].plot(x,self._rsi[bi:ei],label="RSI",color='orange')
            axs[self._rsiInx].axhline(20,color='black',linestyle='--')
            axs[self._rsiInx].axhline(80,color='black',linestyle='--')
        #绘制额外的图表
        while self._showfigure:
            i = 0
            if type(self._config['figure'])==list:
                figures = self._config['figure']
            elif callable(self._config['figure']):
                figures = self._config['figure'](self)
            else:
                break
            if figures is not None:
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
            break
        #一个从外部进行调整图表的手段
        if 'cb' in self._config:
            self._config['cb'](self,axs,bi,ei)
        fig.autofmt_xdate()

        #单独做一个显示层级
        if not self._isupdate:
            self._output = widgets.Output()
            display(self._output)
            self._isupdate = True
        #self._output.clear_output(wait=True)
        #with self._output:
        #    plt.show()
        output_show(self._output)
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
    #pos = '2019-1-1' 直接跳转到该日期
    def show(self,bi=None,ei=None,code2=None,figsize=(32,14),pos=None):
        if self._gotoTrendHeandPos:
            if len(self._k)-self._trendHeadPos>math.floor(self._showcount/2):
                bi = self._trendHeadPos-math.floor(self._showcount/2)
            else:
                bi = len(self._k)-self._showcount
            ei = bi+self._showcount
        if bi is None:
            bi = len(self._k)-self._showcount
        if ei is None:
            ei = len(self._k)
        if bi<0:
            bi = 0
        if ei>len(self._k):
            ei=len(self._k)
        if code2 is not None:
            figsize = (30,8)
            figure2 = Plote(code2,self._period)
        else:
            figure2 = None
        if pos is not None:
            if type(pos)==str:
                if type(self._date[-1][0])==date:
                    post = date.fromisoformat(pos)
                else:
                    post = datetime.fromisoformat(pos)
            else:
                post = pos
                if type(post)==date and type(self._date[-1][0])==datetime:
                    post = datetime(post.year,post.month,post.day)
                elif type(post)==datetime and type(self._date[-1][0])==date:
                    post = date(post.year,post.month,post.day)               
            for i in range(len(self._date)):
                if self._date[i][0]>=post:
                    bi = math.floor(i-self._showcount/2)
                    if bi<=0:
                        bi = 0
                    ei = bi+self._showcount
                    if ei>len(self._date):
                        ei = len(self._date)
                        bi = len(self._date)-self._showcount
                        if bi<0:
                            bi=0
                    self._trendHeadPos = i
                    break

        nextbutton = widgets.Button(description="下一页",layout=Layout(width='96px'))
        prevbutton = widgets.Button(description="上一页",layout=Layout(width='96px'))
        zoominbutton = widgets.Button(description="+",layout=Layout(width='48px'))
        zoomoutbutton = widgets.Button(description="-",layout=Layout(width='48px'))
        
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
 
        if self._period=='d':
            periodDropdownvalue = '日线'
            indexDropdownvalue = 'MACD+'
            mainDropdownvalue = 'TREND'
        elif self._period==120:
            periodDropdownvalue = '120分钟'
            indexDropdownvalue = 'CLEAR'
            mainDropdownvalue = 'CLEAR'
            self._correcttionVolume = True           
        elif self._period==60:
            periodDropdownvalue = '60分钟'
            indexDropdownvalue = 'CLEAR'
            mainDropdownvalue = 'CLEAR'
            self._correcttionVolume = True   
        elif self._period==30:
            periodDropdownvalue = '30分钟'
            indexDropdownvalue = 'CLEAR'
            mainDropdownvalue = 'CLEAR'            
            self._correcttionVolume = True                     
        elif self._period==15:
            periodDropdownvalue = '15分钟'
            indexDropdownvalue = 'MACD'
            mainDropdownvalue = 'TREND'
            self._correcttionVolume = True
        elif self._period==5:
            periodDropdownvalue = '5分钟'
            indexDropdownvalue = 'CLEAR'
            mainDropdownvalue = 'CLEAR'            
            self._correcttionVolume = True
        else:
            periodDropdownvalue = '周线'
            indexDropdownvalue = 'MACD+'
            mainDropdownvalue = 'BOLL+' 
        def config_index(sel):
            if sel=='MACD+':
                self.enable('macd')
                self.enable('energy')
                self.disable('kdj')
                self.disable('best')
                self.disable('bollwidth')
                self.disable('flow')
            elif sel=='KDJ+':
                self.enable('macd')
                self.disable('energy')
                self.enable('kdj')
                self.disable('best')
                self.disable('bollwidth')
                self.disable('flow')
            elif sel=='MACD+Best':
                self.enable('macd')
                self.enable('energy')
                self.disable('kdj')
                self.enable('best')
                self.disable('bollwidth')
                self.disable('flow')
            elif sel=='MACD+BollWidth':
                self.enable('macd')
                self.enable('energy')
                self.disable('kdj')
                self.disable('best')
                self.enable('bollwidth')
                self.disable('flow')
            elif sel=='MACD':
                self.enable('macd')
                self.disable('energy')
                self.disable('kdj')
                self.disable('best')
                self.disable('bollwidth')
                self.disable('flow')
            elif sel=='FLOW':
                self.disable('macd')
                self.disable('energy')
                self.disable('kdj')
                self.disable('best')
                self.disable('bollwidth')
                self.enable('flow')
            elif sel=='CLEAR':
                self.disable('macd')
                self.disable('energy')
                self.disable('kdj')
                self.disable('best')
                self.disable('bollwidth')
                self.disable('flow')
            self.config()    
        def config_main(sel):
            if sel=='BOLL+':
                self.enable('boll')
                self.enable('bigma20')
                self.disable('trend')
                self.enable('ma')
                self.disable('ma')
                self.disable('eps')
            elif sel=='MA':
                self.enable('ma')
                self.disable('boll')
                self.disable('bigma20')
                self.disable('trend')
                #if self._period=='d':
                #    self._config['ma'] = [5,10,60]
                #else:
                #    self._config['ma'] = [5,10]
                self.disable('eps')
            elif sel=='BOLL':
                self.enable('boll')
                self.enable('bigma20')
                self.disable('trend')
                self.disable('ma')
                self.disable('eps')
            elif sel=='TREND':
                self.enable('trend')
                self.disable('bigma20')
                self.disable('boll')
                self.disable('ma')
                self.disable('eps')
            elif sel=='CLEAR':
                self.disable('boll')
                self.disable('bigma20')
                self.disable('trend')
                self.disable('ma')
                self.enable('eps')
            self.config()                     
        b,main_sel = shared.fromRedis('kline.main%s'%str(self._period))
        if b:
            mainDropdownvalue = main_sel
            config_main(main_sel)
        b,index_sel = shared.fromRedis('kline.index%s'%str(self._period))
        if b and indexDropdownvalue != index_sel:
            indexDropdownvalue = index_sel
            config_index(index_sel)
        mainDropdown = widgets.Dropdown(
            options=['BOLL+','MA','BOLL','TREND','CLEAR'],
            value=mainDropdownvalue,
            description='',
            disabled=False,
            layout=Layout(width='96px')
        )    
        indexDropdown = widgets.Dropdown(
            options=['MACD+','KDJ+','MACD+Best','MACD+BollWidth','MACD','FLOW','CLEAR'],
            value=indexDropdownvalue,
            description='',
            disabled=False,
            layout=Layout(width='96px')
        )           
        periodDropdown = widgets.Dropdown(
            options=['日线', '周线', '120分钟','60分钟','30分钟','15分钟','5分钟','5分钟大'],
            value=periodDropdownvalue,
            description='',
            disabled=False,
            layout=Layout(width='96px')
        )
        refreshbutton = widgets.Button(description="刷新",layout=Layout(width='64px'))
        listbutton = widgets.Button(description="列表",layout=Layout(width='64px'))
        codetext = widgets.Text(value=self.code(),description='',layout=Layout(width='96px'))
        #output = widgets.Output()
        b,favorites = shared.fromRedis('favorite_'+str(date.today()))
        isfavorite = False
        favoriteNode = ''
        favoriteContext = ''
        if b:
            for fav in favorites:
                if fav['code']==self.code():
                    isfavorite = True
                    favoriteNode = fav['node']
                    favoriteContext = fav['context']
                    break
        favoritecheckbox = widgets.Checkbox(value=isfavorite,description='关注',disabled=False,layout=Layout(display='block',width='72px'))
        box_layout = Layout(display='flex',
                            flex_flow='wrap',
                            align_items='stretch',
                            border='solid',
                            width='100%')
        if type(self._comarg)==str:
            stockcode = self._comarg
        else:
            stockcode = self._comarg if self._comarg[2]!=':' else self._comarg[0:2]+self._comarg[3:]
        if self._company is not None and len(self._company)>2 and self._company[3]=='EM':
            link = widgets.HTML(value="""<a href="http://quote.eastmoney.com/bk/90.%s.html" target="_blank" rel="noopener">%s(%s)</a>"""%(stockcode,self._company[2],stockcode))
            link2 = widgets.HTML(value="""<a href="http://data.eastmoney.com/bkzj/%s.html" target="_blank" rel="noopener">资金流向</a>"""%(stockcode))
        else:
            link = widgets.HTML(value="""<a href="https://xueqiu.com/S/%s" target="_blank" rel="noopener">%s(%s)</a>"""%(stockcode,self._company[2],stockcode))
            b,eastname = mapxueqiu2east(stockcode)
            if b:
                link2 = widgets.HTML(value="""<a href="http://data.eastmoney.com/%s.html" target="_blank" rel="noopener">资金流向</a>"""%(eastname))
            else:
                link2 = widgets.HTML(value="""<a href="http://data.eastmoney.com/zjlx/%s.html" target="_blank" rel="noopener">资金流向</a>"""%(stockcode[2:]))
            
        items = [prevbutton,nextbutton,zoominbutton,zoomoutbutton,backbutton,slider,frontbutton,mainDropdown,indexDropdown,periodDropdown,refreshbutton,link,link2,favoritecheckbox,codetext]

        if self._keyindex is not None:
            keyprev = widgets.Button(description="<<",layout=Layout(width='48px'))
            keynext = widgets.Button(description=">>",layout=Layout(width='48px'))
            items.append(keyprev)
            items.append(keynext)

        list_output = widgets.Output()
        if self.code()[0] == 'b':
            items.append(listbutton)

        fafavoriteNodeWidget = widgets.Text(
            value=favoriteNode,
            placeholder='输入备注',
            disabled=False
        )
        if isfavorite:
            items.append(fafavoriteNodeWidget)
        if self._showfigure:
            items.append(figuretoggle)
        box = Box(children=items, layout=box_layout)
        
        beginPT = bi
        endPT = ei
        b,sr = shared.fromRedis('kline.zoom%s'%self._period)
        if b:
            showRange = sr
        else:    
            showRange = ei-bi            
        needUpdateSlider = True
        skipUpdate = False
        def showline():
            nonlocal needUpdateSlider
            if not skipUpdate:
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
                if beginPT<0:
                    beginPT = 0
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
                if endPT>len(self._k):
                    endPT = len(self._k)
            self._trendHeadPos = endPT
            setSlider(beginPT,endPT,endPT)
            showline()

        def on_zoomin(b):
            nonlocal beginPT,endPT,showRange
            showRange = math.floor(showRange*2/3)
            shared.toRedis(showRange,'kline.zoom%s'%self._period)
            beginPT = endPT - showRange
            self._trendHeadPos = endPT
            setSlider(beginPT,endPT,endPT)
            showline()

        def on_zoomout(b):
            nonlocal beginPT,endPT,showRange
            showRange = math.floor(showRange*3/2)
            shared.toRedis(showRange,'kline.zoom%s'%self._period)
            beginPT = endPT - showRange
            if beginPT < 0:
                beginPT = 0
                endPT = beginPT+showRange
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

        def on_codetext(e):
            nonlocal link,link2
            c = e['new'].upper()
            if len(c)==8 and c[0]=='S' and (c[1]=='Z' or c[1]=='H'):
                self._comarg = c
                self.reload()
                recalcRange()
                showline()
                refreshbutton.button_style = ''
                stockcode = self._comarg if self._comarg[2]!=':' else self._comarg[0:2]+self._comarg[3:]
                link.value="""<a href="https://xueqiu.com/S/%s" target="_blank" rel="noopener">%s(%s)</a>"""%(stockcode,self._company[2],stockcode)
                b,eastname = mapxueqiu2east(stockcode)
                if b:
                    link2.value="""<a href="http://data.eastmoney.com/%s.html" target="_blank" rel="noopener">资金流向</a>"""%(eastname)
                else:
                    link2.value="""<a href="http://data.eastmoney.com/zjlx/%s.html" target="_blank" rel="noopener">资金流向</a>"""%(stockcode[2:])
                                  
        codetext.observe(on_codetext,names='value')

        def on_sliderChange(event):
            nonlocal needUpdateSlider
            self._trendHeadPos = event['new']
            updateTrend()
            if needUpdateSlider:
                showline()

        def updateTrend():
            if self._macd is not None:
                #当是日线以下数据时使用日线趋势下，先将_trendHeadPos转换为日期然后在重新计算日线趋势线
                if type(self._period)==int:
                    p = self._trendHeadPos
                    if p>=len(self._k):
                        p = len(self._k)-1
                    if p<0:
                        p = 0
                    t = self._date[p][0]
                    code = self.code().upper()
                    _,dk,dd= self.getKlineData(code,'d')
                    for i in range(len(dd)):
                        d = dd[i][0]
                        if d.year==t.year and d.month==t.month and d.day==t.day:
                            p = i
                            break
                    if p<len(dk):
                        m,_,_ = stock.macd(dk)
                        self._trend,last_line,b = trend.macdTrend(dk[:p+1,:],m[:p+1])
                        #如果是日线的趋势线将被保存,用于小级别中绘制
                        self._day_trend = self._trend
                        self._day_date = dd
                        self._day_last_line = last_line
                        self._day_b = b 
                else:
                    if self._trendHeadPos<len(self._k):
                        self._trend,last_line,b = trend.macdTrend(self._k[:self._trendHeadPos+1,:],self._macd[:self._trendHeadPos+1])
                        #如果是日线的趋势线将被保存,用于小级别中绘制
                        if self._period == 'd':
                            self._day_trend = self._trend
                            self._day_date = self._date
                            self._day_last_line = last_line
                            self._day_b = b              

        def on_prev(b):
            nonlocal needUpdateSlider,beginPT,endPT,showRange
            self._trendHeadPos -= 1
            if self._trendHeadPos<0:
                self._trendHeadPos = 0
            needUpdateSlider = False
            if self._trendHeadPos<beginPT-1:#向前移动移动视口
                beginPT = self._trendHeadPos-math.floor(showRange/2)
                if beginPT<0:
                    beginPT = 0
                endPT = beginPT+showRange
                if endPT>len(self._k):
                    endPT = len(self._k)
                setSlider(beginPT,endPT,self._trendHeadPos)
            
            slider.value = self._trendHeadPos
            updateTrend()
            showline()
            
        def on_next(b):
            nonlocal needUpdateSlider,beginPT,endPT,showRange
            self._trendHeadPos += 1
            needUpdateSlider = False
            if self._trendHeadPos>len(self._k):
                self._trendHeadPos = len(self._k)
            if self._trendHeadPos>endPT+1:#向后移动移动视口
                endPT = self._trendHeadPos+math.floor(showRange/2)
                if endPT>len(self._k):
                    endPT = len(self._k)
                beginPT = endPT-showRange
                if beginPT<0:
                    beginPT=0
                setSlider(beginPT,endPT,self._trendHeadPos)
            slider.value = self._trendHeadPos
            updateTrend()
            showline()

        nextbutton.on_click(on_nextbutton_clicked)
        prevbutton.on_click(on_prevbutton_clicked)

        def gotopos(p):
            nonlocal needUpdateSlider,beginPT,endPT,showRange
            if p>=0 and p<len(self._k):
                self._trendHeadPos = p
                needUpdateSlider = False
                if self._trendHeadPos>endPT or self._trendHeadPos<beginPT:
                    endPT = self._trendHeadPos+math.floor(showRange/2)
                    if endPT>len(self._k):
                        endPT = len(self._k)
                    beginPT = endPT-showRange
                    if beginPT<0:
                        beginPT=0
                    setSlider(beginPT,endPT,self._trendHeadPos)
                slider.value = self._trendHeadPos
                updateTrend()
                showline()

        def on_keyprev(e):
            previ = 0
            for p in self._keyindex:
                if p>=self._trendHeadPos:
                    break
                previ = p
            if previ!=0:
                gotopos(previ)
            
        def on_keynext(e):
            nexti = 0
            nx = 0
            for p in self._keyindex:
                if p>=self._trendHeadPos:
                    if nx==1:
                        nexti = p
                        break
                    nx = 1
            if nexti!=0:
                gotopos(nexti)
            
        if self._keyindex is not None:
            keyprev.on_click(on_keyprev)
            keynext.on_click(on_keynext)
        zoominbutton.on_click(on_zoomin)
        zoomoutbutton.on_click(on_zoomout)

        def recalcRange(resetpos=True):
            nonlocal beginPT,endPT,showRange
            endPT = len(self._k)
            beginPT = len(self._k)-showRange
            if beginPT<0:
                beginPT = 0
            if resetpos:
                if self._trendHeadPos<0 or self._trendHeadPos>len(self._k):
                    self._trendHeadPos = endPT-1
            setSlider(beginPT,endPT,self._trendHeadPos)
        needRecalcRange = False

        def on_index(e):
            sel = e['new']
            shared.toRedis(sel,'kline.index%s'%self._period)
            shared.toRedis(mainDropdown.value,'kline.main%s'%self._period)
            config_index(sel)
            nonlocal needRecalcRange
            if needRecalcRange:
                recalcRange()
                needRecalcRange = False
            showline()            
        indexDropdown.observe(on_index,names='value')
           
        def on_main(e):
            sel = e['new']
            shared.toRedis(indexDropdown.value,'kline.index%s'%self._period)
            shared.toRedis(sel,'kline.main%s'%self._period)
            config_main(sel)
            showline()

        mainDropdown.observe(on_main,names='value')           
        def on_period(e):
            nonlocal needRecalcRange,skipUpdate,beginPT,endPT,showRange
            name2peroid = {
                '日线':['d',False,False],
                '周线':['w',False,False],
                '120分钟':[120,False,True],
                '60分钟':[60,False,True],
                '30分钟':[30,False,True],
                '15分钟':[15,False,True],
                '5分钟':[5,False,True],
                '5分钟大':[5,True,True]
            }
            period = e['new']
            
            pbi = self._date[endPT-1][0]
            sel = name2peroid[period]
            self._period = sel[0]
            if sel[0]==5:
                shared.toRedis(sel[1],'kline.big5')
            shared.toRedis(self._period,'kline.period')
            self._big5mode = sel[1]
            if e['old']:
                old = name2peroid[e['old']]
                if sel[2] != old[2] and self._timer is not None:
                    xueqiu.cancelTimeout(self._timer)
                    startTimer()

            self.reload()
            #日线和周线切换为MACD+,其他切换为MACD
            #日线和周线切换到BULL+,其他期货到TREND
            b,sr = shared.fromRedis('kline.zoom%s'%self._period)
            if b:
                showRange = sr
            b1,main_sel = shared.fromRedis('kline.main%s'%self._period)
            b2,index_sel = shared.fromRedis('kline.index%s'%self._period)
            if b1 and b2:
                skipUpdate = True
                config_main(main_sel)
                mainDropdown.value = main_sel
                config_index(index_sel)
                indexDropdown.value = index_sel
            elif sel[2]:
                if indexDropdown.value!="CLEAR":
                    skipUpdate = True
                    needRecalcRange = True
                    if type(self._period)==int and indexDropdown.value=='CLEAR':
                        indexDropdown.value = "CLEAR"    
                    else:
                        indexDropdown.value = "FLOW"
                if mainDropdown.value=="BOLL+":
                    skipUpdate = True
                    needRecalcRange = True
                    mainDropdown.value="TREND"
            else:
                if indexDropdown.value != "MACD+":
                    skipUpdate = True
                    needRecalcRange = True
                    indexDropdown.value = "MACD+"
                if mainDropdown.value=="TREND":
                    skipUpdate = True
                    needRecalcRange = True
                    mainDropdown.value="BOLL+"                
            skipUpdate = False
            #recalcRange()
            #在切换时序时保持查看日期的位置尽量不变
            beginPT = 0
            for i in range(len(self._date)):
                if type(pbi) == type(self._date[i][0]):
                    if pbi <= self._date[i][0]:
                        beginPT = i
                        break
                else:
                    if date(pbi.year,pbi.month,pbi.day) <= date(self._date[i][0].year,self._date[i][0].month,self._date[i][0].day):
                        beginPT = i
                        break
            endPT = beginPT+showRange
            if endPT>=len(self._k):
                recalcRange()
            showline()

        periodDropdown.observe(on_period,names='value')

        def refresh(b):
            self.reload(all=False)
            recalcRange()
            showline()
            refreshbutton.button_style = ''
        refreshbutton.on_click(refresh)

        def on_list(e):
            #https://stock.xueqiu.com/v5/stock/forum/stocks.json?ind_code=BK0021
            uri = """https://stock.xueqiu.com/v5/stock/forum/stocks.json?ind_code=%s"""%(self.code().upper())
            b,r = xueqiu.xueqiuJson(uri)
            if b:
                if 'data' in r:
                    companys = r['data']['items']
                    list_output.clear_output()
                    with list_output:
                        for com in companys:
                            Plote(com['symbol'],'d',config={'index':True},mode='runtime').show()
        listbutton.on_click(on_list)
        backbutton.on_click(on_prev)
        frontbutton.on_click(on_next)
        slider.observe(on_sliderChange,names='value')
            
        if self._showfigure:
            figuretoggle.observe(on_change,names='value')

        display(box)
        self.showKline(beginPT,endPT,figsize=figsize)
        if self.code()[0]=='b':
            display(list_output)        
        if figure2 is not None:
            bi = figure2.date2index( self.index2date(beginPT) )
            ei = figure2.date2index( self.index2date(endPT) )
            if bi != ei:
                figure2.showKline(bi,ei,figsize=figsize)

        def on_favorite(e):
            today = date.today()
            name = 'favorite_'+str(today)
            b,favorites = shared.fromRedis(name)
            if not b:
                favorites = []
            code = self.code()
            if e['new']:
                favorites.append({
                    'date':today,
                    'code':code,
                    'name':self.name(),
                    'node':fafavoriteNodeWidget.value,
                    'context':self._context
                })
                stock.execute("insert into notebook (date,code,name,context,note) values ('%s','%s','%s','%s','%s')"%(stock.dateString(today),code,self.name(),self._context if self._context is not None else '',fafavoriteNodeWidget.value))
                box.children = list(box.children)+[fafavoriteNodeWidget]
            else:
                for fav in favorites[:]:
                    if fav['code']==code:
                        favorites.remove(fav)
                        break
                stock.execute("delete from notebook where date='%s' and code='%s'"%(stock.dateString(today),code))
                box.children = box.children[:-1]
            shared.toRedis(favorites,name,ex=24*3600)

        favoritecheckbox.observe(on_favorite,names='value')
        
        updateFavoriteTimer = None
        def on_favoriteText(e):
            nonlocal updateFavoriteTimer
            if updateFavoriteTimer is not None:
                #updateFavoriteTimer.cancel()
                xueqiu.cancelTimeout(updateFavoriteTimer)
            def updateFavoriteText():
                today = date.today()
                code = self.code()
                stock.execute("update notebook set note=N'%s' where date='%s' and code='%s'"%(fafavoriteNodeWidget.value,stock.dateString(today),code))
                name = 'favorite_'+str(today)
                b,favorites = shared.fromRedis(name)
                if b:
                    for fav in favorites[:]:
                        if fav['code']==code:
                            fav['node']=fafavoriteNodeWidget.value
                            break
                    shared.toRedis(favorites,name,ex=24*3600)
            updateFavoriteTimer = xueqiu.setTimeout(3,updateFavoriteText,'favorite%s'%self.code())

        fafavoriteNodeWidget.observe(on_favoriteText,names='value')
        def update():
            for i in range(10):
                refreshbutton.button_style = 'success' #green button
                try:
                    self.reload(all=False)
                except Exception as e:
                    mylog.printe(e)
                recalcRange(False)
                try:    
                    showline()
                except Exception as e:
                    mylog.printe(e)
                refreshbutton.button_style = ''
                try:
                    startTimer()
                except Exception as e:
                    mylog.printe(e)
                break

        def startTimer():
            if stock.isTransTime():
                nt = xueqiu.next_k_date(5)
            else:
                nt = 0 #xueqiu.next_k_date(self._period)
            if nt>0:
                self._timer = xueqiu.setTimeout(nt+1,update,'kline%s'%self.code())
        startTimer()