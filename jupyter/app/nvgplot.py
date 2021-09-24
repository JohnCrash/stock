from ctypes import c_float
from sdl2.keycode import SDLK_KP_LESS
from .nanovg import frame,vg
from . import monitor,xueqiu,stock,shared,mylog,trend
from pypinyin import pinyin, Style
from datetime import date,datetime,timedelta
import numpy as np
from numpy.core.numeric import NaN
import threading
import math
import sdl2
from OpenGL import GL
import win32api
import ctypes

log = mylog.init('nvgplot.log',name='nvgplot')
def pinyinhead(s):
    r = ''
    for z in s:
        v = pinyin(z, style=Style.TONE3)
        if len(v)>0 and len(v[0])>0:
            r += v[0][0][0]
    return r.upper()
def intercolor(b,e,f):
    """
    起始颜色b,结束颜色e ,f=0-1 计算中间颜色
    """
    return ((e[0]-b[0])*f+b[0],(e[1]-b[1])*f+b[1],(e[2]-b[2])*f+b[2])
def f2color255(c):
    return (int(c[0]*255),int(c[1]*255),int(c[2]*255))
def strong2color(s):
    """
    将强度映射成颜色 s = [-1,1]
    """
    rgb = []
    for b in range(255,0,-1):#紫色到红到
        rgb.append((255,0,b))
    for g in range(255): #红到黄
        rgb.append((255,g,0))
    for r in range(255,0,-1): #红到绿
        rgb.append((r,255,0))
    for b in range(255): #绿的青
        rgb.append((0,255,b))
    if s>1:
        s=1
    if s<-1:
        s=-1
    i = int((1-(s+1)/2)*(len(rgb)-1))

    return rgb[i]
"""
返回30日均线向上，股价低于n日均线的分类或者个股
p = '90' ,'91'
"""
def get30codes(p,n,maN=30):
    K,D = xueqiu.get_period_k(240)
    c = xueqiu.get_company_select()
    maB = stock.maMatrix(K,maN)
    maL = stock.maMatrix(K,n)
    R = []
    for i in range(len(c)):
        if maB[i,-1]>=maB[i,-2] and K[i,-1]<=maL[i,-1] and c[i][3]==p:
            R.append(c[i][1])
    return R

"""
判断向上或者向下发散
"""
def ismafashan(mas):
    ma5,ma10,ma20,ma30 = mas
    if ma5[-1]>ma5[-2] and ma10[-1]>ma10[-2] and ma20[-1]>ma20[-2] and ma30[-1]>ma30[-2]:
        return True
    if ma5[-1]<ma5[-2] and ma10[-1]<ma10[-2] and ma20[-1]<ma20[-2] and ma30[-1]<ma30[-2]: 
        return True
    return False

"""
用来判断多点拟合线
"""
def isrise(k):
    x = np.empty((len(k),2))
    x[:,0] = np.arange(len(k))
    x[:,1] = k
    line = trend.lastSequaresLine(x)
    return line[0]>=0
"""
分析早盘情况
k5 (0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting
"""
def zpfx(k5,d5):
    R = []
    mx = -1
    for i in range(len(d5)-1):
        if d5[i][0].day!=d5[i+1][0].day or i==0:
            for j in range(i,i+48,12):
                if j+12<len(d5) and k5[j]>0:
                    r = (k5[j+12]-k5[j])/k5[j]
                    if abs(r)>mx:
                        mx = abs(r)
                    R.append((r,i,j-i))
    if mx!=-1:
        fz = mx*0.8
        for i in range(len(R)-1,0,-1):
            if R[i][2]==0 and abs(R[i][0])>fz:
                return (R[i][0],(len(R)-1-i)/4)
    return None

class ThemosDefault:
    BGCOLOR = (0.95,0.95,0.95,1) #图表背景颜色

    MA60_COLOR = vg.nvgRGB(255,128,60) #ma60颜色
    PRICE_COLOR = vg.nvgRGB(70,130,200) #价格颜色
    MAIN_COLOR = vg.nvgRGB(255,0,255) #主力
    HUGE_COLOR = vg.nvgRGB(139,0,0)
    LARG_COLOR = vg.nvgRGB(255,0,0)
    MA5_COLOR = vg.nvgRGB(255,0,255)
    MA30_COLOR = vg.nvgRGB(0,0,255)
    MID_COLOR = vg.nvgRGB(255,215,0)
    TING_COLOR = vg.nvgRGB(135,206,250)
    RED_COLOR = vg.nvgRGB(220,0,0)   #涨
    GREEN_COLOR = vg.nvgRGB(0,120,0) #跌
    RED_KCOLOR = vg.nvgRGB(250,0,0)  
    GREEN_KCOLOR = vg.nvgRGB(0,244,244)      
    BG_COLOR = vg.nvgRGB(255,255,255) #背景
    CROSS_COLOR = vg.nvgRGBAf(1,1,1,0.5)
    YLABELWIDTH = 40   #y轴坐标轴空间
    XLABELHEIGHT = 30  #x轴坐标轴空间

    ORDER_BGCOLOR = vg.nvgRGB(220,220,220)
    ORDER_HEADCOLOR = vg.nvgRGB(64,96,196)
    ORDER_SELCOLOR = vg.nvgRGB(196,96,96)
    ORDER_TEXTBGCOLOR = vg.nvgRGBA(64,64,64,255)
    ORDER_TEXTCOLOR = vg.nvgRGB(255,255,255)  
    ORDER_TEXTCOLOR2 = vg.nvgRGB(255,255,0)
    ORDER_TEXTCOLOR3 = vg.nvgRGB(0,255,0)
    CAN_BUY_TEXTCOLOR = vg.nvgRGB(170,0,0)  #上轨和中轨向上
    CAN_BUY_TEXTCOLOR2 = vg.nvgRGB(70,0,140)  #都向上
    CAN_BUY_TEXTCOLOR3 = vg.nvgRGB(187,61,0)  #仅仅下轨向上
    WARN_BUY_COLOR = vg.nvgRGB(255,255,0)
    WARN_NEWHIGH_COLOR = vg.nvgRGB(255,128,255)
    WARN_SELL_COLOR = vg.nvgRGB(0,255,64)
    ORDER_WIDTH = 150       #排序栏宽度
    ORDER_ITEM_HEIGHT = 24  #排序栏按钮高度
    ORDER_FONTSIZE = 14

    AXISCOLOR = vg.nvgRGBf(0.9,0.9,0.9)
    GRIDCOLOR = vg.nvgRGBf(0.15,0.15,0.15)
    TEXTCOLOR = vg.nvgRGBf(1,1,1)

    SELBGCOLOR = vg.nvgRGBf(0,0.1,0.1)
class ThemosBlack:
    BGCOLOR = (0.0,0.0,0.0,1) #图表背景颜色

    MA60_COLOR = vg.nvgRGB(255,128,60) #ma60颜色
    PRICE_COLOR = vg.nvgRGB(70,130,200) #价格颜色
    MAIN_COLOR = vg.nvgRGB(255,0,255) #主力
    HUGE_COLOR = vg.nvgRGB(139,0,0)
    LARG_COLOR = vg.nvgRGB(255,128,0)
    MA5_COLOR = vg.nvgRGB(255,0,255)
    MA10_COLOR = vg.nvgRGB(240,248,136)
    MA20_COLOR = vg.nvgRGB(0,178,240)
    MA30_COLOR = vg.nvgRGB(0,128,255)
    MID_COLOR = vg.nvgRGB(255,215,0)
    TING_COLOR = vg.nvgRGB(135,206,250)
    RED_COLOR = vg.nvgRGB(250,0,0)  
    GREEN_COLOR = vg.nvgRGB(0,200,0) 
    RED_KCOLOR = vg.nvgRGB(250,0,0)  
    GREEN_KCOLOR = vg.nvgRGB(0,244,244)  
    BG_COLOR = vg.nvgRGB(0,0,0) #背景
    CROSS_COLOR = vg.nvgRGBAf(1,1,1,0.5)
    YLABELWIDTH = 42   #y轴坐标轴空间
    XLABELHEIGHT = 36  #x轴坐标轴空间

    ORDER_BGCOLOR = vg.nvgRGB(0,0,0)
    ORDER_HEADCOLOR = vg.nvgRGB(0,0,0)
    ORDER_SELCOLOR = vg.nvgRGB(32,96,168)
    ORDER_TEXTBGCOLOR = vg.nvgRGBA(0,0,0,255)
    ORDER_TEXTCOLOR = vg.nvgRGB(255,255,255) 
    ORDER_TEXTCOLOR2 = vg.nvgRGB(255,255,0) 
    ORDER_TEXTCOLOR3 = vg.nvgRGB(0,255,0)
    CAN_BUY_TEXTCOLOR = vg.nvgRGB(170,0,0)  #上轨和中轨向上
    CAN_BUY_TEXTCOLOR2 = vg.nvgRGB(70,0,140)  #都向上
    CAN_BUY_TEXTCOLOR3 = vg.nvgRGB(100,50,0)  #仅仅下轨向上

    WARN_BUY_COLOR = vg.nvgRGB(64,0,0)
    WARN_BUY_COLOR2 = vg.nvgRGB(128,0,0)
    WARN_NEWHIGH_COLOR = vg.nvgRGB(64,64,0)
    WARN_SELL_COLOR = vg.nvgRGB(0,64,0)
    WARN_SELL_COLOR2 = vg.nvgRGB(0,128,0)
    ORDER_WIDTH = 160       #排序栏宽度
    ORDER_ITEM_HEIGHT = 24  #排序栏按钮高度
    ORDER_FONTSIZE = 14

    AXISCOLOR = vg.nvgRGBf(0.9,0.9,0.9)
    GRIDCOLOR = vg.nvgRGBf(0.15,0.15,0.15)
    TEXTCOLOR = vg.nvgRGBf(1,1,1)

    SELBGCOLOR = vg.nvgRGBf(0,0,0.1)

Themos = ThemosBlack
class StockPlot:
    """
    包括两个区域，分时和成交量流入流出区
    """
    KD = stock.query("select date from kd_xueqiu where id=8828")
    MA = 1 #均线5,20,60
    FLOW = 1 #大资金流向
    VOL = 2  #成交量显示
    LMR = 3  #成交量比
    RT = 0  #更新RT
    K = 1 
    BOLLWAY = 2
    KVMODE = 0
    c_float_p = ctypes.POINTER(ctypes.c_float)
    def __init__(self):
        self._kplot = frame.Plot()
        self._vplot = frame.Plot()
        self._fplot = frame.Plot()
        self._kplot.setThemos(Themos)
        self._vplot.setThemos(Themos)
        self._fplot.setThemos(Themos)
        self._code = None
        self._k = None
        self._d = None
        self._mm = None 
        self._forcus = False
        self._kbi = None
        self._kei = None
        self._bollway = None
        self._kmode = StockPlot.MA
        self._vmode = StockPlot.FLOW
        self._upmode = StockPlot.RT
        self._period = None
        self._needrender = False
    def clear(self):
        self._code = None
        self._k = None
        self._d = None
        self._mm = None 
        self._kplot.setTitle('')
        self._kplot.clear()
        self._vplot.clear()
        self._fplot.clear()
    def forcus(self,b):
        self._forcus = b
    def getFlow(self,code,d,after):
        flowk,flowd = xueqiu.getFlowCache(code,bi=after)
        if flowk is None or flowd is None:
            return None
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
    def getKlineData(self,code,period,knum,off):
        KDN = len(StockPlot.KD)
        if period==5 or period=='d':
            bi = KDN-off-knum-60 #确保60日均线计算是正确的
            if bi<0:
                bi=0
            after = stock.dateString(StockPlot.KD[bi][0])
            c,k,d = stock.loadKlineCache(code,period,bi=after)
        else:
            bi = KDN-math.ceil((off+knum+320)/(240/period))
            if bi<0:
                bi=0
            after = stock.dateString(StockPlot.KD[bi][0])
            c,k,d = stock.loadKlineCache(code,5,bi=after)
            if period!=5:
                k,d = stock.mergeK(k,d,int(period/5))
        
        if off==0 and stock.isTransDay():
            _,k,d = xueqiu.appendK(code,period,k,d)
        if off!=0:
            k = k[:-off]
            d = d[:-off]
        #叠加流入数据
        if d is not None and len(d)>0:
            flow = self.getFlow(code,d,after)
            if flow is not None and period!='d' and period!=60: #去掉一天中最后的数据，绘制的时候不然⑦链接
                for i in range(1,len(d)):
                    if d[i][0].day!=d[i-1][0].day:
                        flow[i,:] = NaN
        else:
            flow = None
        return c,k,d,flow
    def updateK(self,code,label,period,knum,kei,item=None): #更新K线图
        self._code = code
        self._upmode = StockPlot.K
        self._period = period
        _,k,d,flow = self.getKlineData(code,period,knum,kei)

        bi = -knum
        ei = k.shape[0]
        
        x = np.arange(len(k[bi:ei]))
        xticks = []
        D = d[bi:]
        for i in range(1,len(D)):
            if type(period)==int:
                if (D[i][0].day!=D[i-1][0].day):
                    t = D[i][0]
                    xticks.append((i,'%2d-%2d'%(t.month,t.day)))        
            else:
                if D[i][0].weekday()==0:
                    t = D[i][0]
                    xticks.append((i,'%2d-%2d'%(t.month,t.day)))                   
        self._kplot.setx(x)
        self._kplot.setTicks(xticks)
        K = k[bi:,1:]
        self._k = k[bi:]
        self._d = d[bi:]
        self._kplot.plot(K,color=Themos.PRICE_COLOR,style=frame.Plot.K)
        if StockPlot.KVMODE==1:
            if period=='d':
                ma5 = stock.ma(k[:,4],5)
                ma20 = stock.ma(k[:,4],20)
                ma30 = stock.ma(k[:,4],30)
            else:
                s = int(15*80/period)
                ma5 = stock.ma(k[:,4],s)
                ma20 = stock.ma(k[:,4],4*s)
                ma30 = stock.ma(k[:,4],6*s)            
            self._kplot.plot(ma5[bi:],label='ma5',color=Themos.MAIN_COLOR,linewidth=1)
            self._kplot.plot(ma20[bi:],label='ma20',color=Themos.LARG_COLOR,linewidth=2)
            self._kplot.plot(ma30[bi:],label='ma30',color=Themos.MA30_COLOR,linewidth=3)
        else:
            bo = stock.boll(k[:,4])
            self._kplot.plot(bo[bi:,0],label='low',color=Themos.MAIN_COLOR,linewidth=1)
            self._kplot.plot(bo[bi:,1],label='mid',color=Themos.PRICE_COLOR,linewidth=1)
            self._kplot.plot(bo[bi:,2],label='up',color=Themos.LARG_COLOR,linewidth=1)
        self._fplot.setx(x)
        self._fplot.setTicks(xticks)      
        self._fplot.setTicksAngle(25)
        if self._vmode==StockPlot.FLOW:
            if flow is not None:
                self._fplot.plot(flow[bi:,0],label='larg',color=Themos.HUGE_COLOR,linewidth=1)
                self._fplot.plot(flow[bi:,1],label='big',color=Themos.LARG_COLOR,linewidth=1)
                self._fplot.plot(flow[bi:,2],label='mid',color=Themos.MID_COLOR,linewidth=1)
                self._fplot.plot(flow[bi:,3],label='ting',color=Themos.TING_COLOR,linewidth=1)
                self._fplot.plot(flow[bi:,0]+flow[bi:,1],label='main',color=Themos.MAIN_COLOR,linewidth=2)
        elif self._vmode==StockPlot.VOL: #这里解释为MACD
            macd,dif,dea = stock.macd(k)
            mp = np.copy(macd[bi:])
            mp[mp<0] = 0
            mn = np.copy(macd[bi:])
            mn[mn>0] = 0            
            self._fplot.plot(mp[bi:],label='macd',color=Themos.RED_COLOR,linewidth=1,style=frame.Plot.BAR)
            self._fplot.plot(mn[bi:],label='macd',color=Themos.GREEN_COLOR,linewidth=1,style=frame.Plot.BAR)
            self._fplot.plot(dif[bi:],label='DIF',color=Themos.LARG_COLOR,linewidth=1)
            self._fplot.plot(dea[bi:],label='DEA',color=Themos.PRICE_COLOR,linewidth=1)
        elif self._vmode==StockPlot.LMR: #这里解释为RSI
            rsi = stock.rsi(k[:,4],6)
            self._fplot.plot(rsi[bi:],label='RSI',color=Themos.LARG_COLOR,linewidth=1)
            self._fplot.hline(20,color=Themos.RED_COLOR,linestyle=(4,2,0))
            self._fplot.hline(80,color=Themos.GREEN_COLOR,linestyle=(4,2,0))
            cci = stock.cci(k)
            self._fplot.plot(stock.zoomrange(cci[bi:],0,100),label='CCI',color=Themos.PRICE_COLOR,linewidth=1)
        self._vplot.setx(x)
        self._vplot.setTicks(xticks)
        self._vplot.setTicksAngle(25)
        color = [Themos.RED_COLOR if K[i,0]<K[i,3] else Themos.GREEN_KCOLOR for i in range(K.shape[0])]
        self._vplot.plot(k[bi:,0],color=color,style=frame.Plot.BAR)
        self._kplot.setGrid(True,True)
        self._vplot.setGrid(True,True)
        self._fplot.setGrid(True,True)
        self._kplot.setTitle(label)
        self._kplot.setZD(item[1])
        self._kplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        self._vplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        self._fplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        self._kplot.setInnerSpace(10,10,0,0)
        self._vplot.setInnerSpace(10,10,0,0)
        self._fplot.setInnerSpace(10,10,0,0)
        
        self._needrender = True
        return kei
    def viewMode(self,km=None,vm=None):
        if km is not None:
            self._kmode = km
        if vm is not None:
            self._vmode = vm
    def update(self,code,label,ok,od,ma5b=None,ma60b=None,isem933=False,item=None): #更新线图
        self._upmode = StockPlot.RT
        self._period = None
        self.clear()
        self._code = code
        self._mm = []
        k = ok[-255*3:]
        d = od[-255*3:]
        self._k = k
        self._d = d
        j = len(d)-1
        if isem933:
            kk = self._k[:,1]
            kk = kk[kk==kk]
            if len(kk)>0:
                self._mm.append((np.argmin(kk),np.argmax(kk)))
        else:
            for i in range(len(d)-1,1,-1):
                if d[i].day!=d[i-1].day:
                    bi = i
                    for bi in range(i,len(d)):#排除盘前
                        if d[bi].minute>29:
                            break
                    if bi<j:
                        self._mm.append((np.argmin(self._k[bi:j,1])+bi,np.argmax(self._k[bi:j,1])+bi))
                    j = i
        x = np.arange(len(d))
        xticks = []
        if isem933:
            for i in range(len(d)):
                if d[i].minute%5==0:
                    t = d[i]
                    if len(xticks)==0 or i-xticks[-1][0]>12:
                        xticks.append((i,'%02d:%02d'%(t.hour,t.minute)))
        else:
            for i in range(len(d)):
                if (d[i].hour==9 and d[i].minute==30) or (d[i].hour==13 and d[i].minute==0):
                    t = d[i]
                    xticks.append((i,'%2d %02d:%02d'%(t.day,t.hour,t.minute)))
        self._kplot.setx(x)
        self._kplot.setTicks(xticks)
        self._kplot.plot(k[:,0],color=Themos.PRICE_COLOR)
        if ma60b is None:
            self._kplot.plot(stock.ma(k[:,0],60),color=Themos.MA60_COLOR,linestyle=(4,2,0))
        else:
            ma60 = np.zeros((len(d),)) #5秒数据更加精确的60均线
            ma60[0] = ma60b[-1]
            N = 240*5
            M = 12
            for i in range(1,len(k)):
                ma60[i] = ma60[i-1]+(k[i,0]-ma60b[int(i/M)-60])/(N) #这是一个近似迭代
            self._kplot.plot(ma60,color=Themos.MA60_COLOR,linestyle=(4,2,0))
        self._vplot.setx(x)
        self._vplot.setTicks(xticks)
        self._vplot.setTicksAngle(25)
        if self._vmode==StockPlot.FLOW:
            self._vplot.plot(k[:,3]+k[:,4],color=Themos.MAIN_COLOR)
            self._vplot.plot(k[:,3],color=Themos.HUGE_COLOR)
            self._vplot.plot(k[:,4],color=Themos.LARG_COLOR)
            self._vplot.plot(k[:,5],color=Themos.MID_COLOR)
            self._vplot.plot(k[:,6],color=Themos.TING_COLOR)
        elif self._vmode==StockPlot.VOL:
            vol = np.zeros((k.shape[0],))
            vol[1:] = k[1:,2]-k[:-1,2]
            vol[vol<0] = 0
            self._vplot.plot(vol,color=Themos.PRICE_COLOR,style=frame.Plot.BAR)
        elif self._vmode==StockPlot.LMR: #量比
            yv = np.zeros((k.shape[0],))
            ov = ok[:-255,2]
            if ov.shape[0]>yv.shape[0]:
                yv = ov[yv.shape[0]:]
            else:
                yv[-ov.shape[0]:] = ov
            self._vplot.plot(yv,color=Themos.MID_COLOR)
            self._vplot.plot(k[:,2],color=Themos.AXISCOLOR)
        self._kplot.setGrid(True,True)
        self._vplot.setGrid(True,True)
        self._kplot.setTitle(label)
        self._kplot.setZD(item[1])
        self._kplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        self._vplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        self._kplot.setInnerSpace(0,0,0,0)
        self._vplot.setInnerSpace(0,0,0,0)    
        if ma5b is not None and len(d)>0:
            ma5 = np.zeros((len(k),))
            ma5[0] = ma5b[0]
            k15b = ma5b[1]
            N = 240*5
            M = 15
            for i in range(1,len(k)):
                ma5[i] = ma5[i-1]+(k[i,0]-k15b[int(i/M)])/(N) #这是一个近似迭代
            self._kplot.plot(ma5,color=Themos.MA5_COLOR,linewidth=2,linestyle=(6,3,0))
        self._needrender = True
    def updateBollWay(self,code,label,k,d,period):
        self._code = code
        self._period = None
        self._upmode = StockPlot.BOLLWAY
        x = np.arange(len(d))
        xticks = []
        for i in range(1,len(d)):
            t = d[i][0]
            if period=='d':
                if t.weekday()==0:
                    xticks.append((i,'%2d-%2d'%(t.month,t.day)))
            else:
                if t.day!=d[i-1][0].day:
                    xticks.append((i,'%2d-%2d'%(t.month,t.day)))
        self._kplot.setx(x)
        self._kplot.plot(k,color=Themos.PRICE_COLOR)
        self._kplot.setTicks(xticks)
        self._kplot.setTicksAngle(25)      
        self._kplot.setGrid(True,True)  
        self._kplot.setTitle(label)
        K = k
        D = d
        self._bollway = None
        for j in range(-1,-len(K),-1):
            b,(n,mink,maxk,zfn) = stock.bollwayex(K[:j])
            if b: #绘制发现的第一个通道
                exbi,exei,mink,maxk = stock.extway(K[:],j,n,mink,maxk)
                tbi = D[exbi][0]
                tei = D[exei][0]                        
                bi,ei = stock.get_date_i(D,tbi,tei)
                self._bollway = (bi,ei,mink,maxk)
                break
        self._needrender = True

    def render(self,canvas,x,y,w,h,xaxis=False,scale=1,warnings=None):
        if self._needrender:
            #绘制背景
            canvas.beginPath()
            canvas.fillColor(Themos.BG_COLOR)
            canvas.rect(x,y,w,h+(Themos.YLABELWIDTH if xaxis else 0))
            canvas.fill()              
            if self._upmode==StockPlot.RT or self._upmode==StockPlot.K:
                self.renderRTK(canvas,x,y,w,h,xaxis=xaxis,scale=scale,warnings=warnings)
            elif self._upmode==StockPlot.BOLLWAY:
                self.renderBollWay(canvas,x,y,w,h,xaxis=xaxis,scale=scale)
            self._needrender = False
    def renderBollWay(self,canvas,x,y,w,h,xaxis=False,scale=1):
        self._kplot.setAxisVisiable(xaxis,True)
        self._kplot.setLineWidthScale(scale)
        self._kplot.render(canvas,x,y,w,h)
        if self._bollway is not None: #绘制通道矩形
            canvas.beginPath()
            xx0 = self._kplot.xAxis2wx(self._bollway[0])
            xx1 = self._kplot.xAxis2wx(self._bollway[1])
            yy0 = self._kplot.yAxis2wy(self._bollway[2])
            yy1 = self._kplot.yAxis2wy(self._bollway[3])
            canvas.strokeColor(Themos.MID_COLOR)
            canvas.strokeWidth(1*scale)
            canvas.rect(xx0,yy0,xx1-xx0,yy1-yy0)
            canvas.stroke()
            canvas.fontFace('sans')
            canvas.fontSize(16)
            canvas.fillColor(Themos.MAIN_COLOR)
            canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_BOTTOM)
            canvas.text(xx0,yy1-5,"%.02f%%"%(100*(self._bollway[3]-self._bollway[2])/self._bollway[2]))
    def renderRTK(self,canvas,x,y,w,h,xaxis=False,scale=1,warnings=None):
        if self._forcus:
            canvas.beginPath()
            canvas.fillColor(Themos.SELBGCOLOR)
            canvas.rect(x+Themos.YLABELWIDTH,y,w-Themos.YLABELWIDTH,h)
            canvas.fill()
        self._kplot.setAxisVisiable(False,True)

        if self._forcus:
            scale = 1
        self._kplot.setLineWidthScale(scale)
        self._vplot.setLineWidthScale(scale)
        if self._upmode==StockPlot.RT:
            self._vplot.setAxisVisiable(xaxis,True)
            self._fplot.setAxisVisiable(False,True)
            self._kplot.render(canvas,x,y,w,h*2/3)
            self._vplot.render(canvas,x,y+h*2/3,w,h/3)
        else:
            self._vplot.setAxisVisiable(False,True)
            self._fplot.setAxisVisiable(xaxis,True)            
            self._fplot.setLineWidthScale(scale)
            self._kplot.render(canvas,x,y,w,h*1/2)
            self._vplot.render(canvas,x,y+h*1/2,w,h/4)
            self._fplot.render(canvas,x,y+h*3/4,w,h/4)

        if self._upmode==StockPlot.RT and self._k is not None: #显示每天的高点和低点
            lasti = self._k.shape[0]-1
            for it in self._mm:
                maxx = self._kplot.xAxis2wx(it[1])
                minx = self._kplot.xAxis2wx(it[0])
                maxy = self._kplot.yAxis2wy(self._k[it[1],0])
                miny = self._kplot.yAxis2wy(self._k[it[0],0])
                canvas.fontFace('sans')
                canvas.fontSize(14)
                if lasti-it[0]>10:
                    canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_TOP)
                    r = self._k[it[0],1]
                    canvas.fillColor(Themos.RED_COLOR if r>0 else Themos.GREEN_COLOR)
                    canvas.text(minx,miny+5,"%.02f%%"%r)
                if lasti-it[1]>10:
                    canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_BOTTOM)
                    r = self._k[it[1],1]
                    canvas.fillColor(Themos.RED_COLOR if r>0 else Themos.GREEN_COLOR)
                    canvas.text(maxx,maxy-5,"%.02f%%"%r)
            canvas.textAlign(vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_BOTTOM)
            for i in range(lasti,0,-1): #em933最后数据有可能是NaN，向前搜索直到找到正确的值
                r = self._k[i,1]
                if r==r:
                    xx = self._kplot.xAxis2wx(i)
                    yy = self._kplot.yAxis2wy(self._k[i,0])
                    canvas.fillColor(Themos.RED_COLOR if r>0 else Themos.GREEN_COLOR)
                    canvas.text(xx,yy-5,"%.02f%%"%r)
                    break
    def getglidingidx(self,d): #返回压制点
        p = []
        maxd = -1e10
        maxi = 0
        for i in range(len(d)):
            if d[i]>=0:
                if d[i]>maxd:
                    maxd = d[i]
                    maxi = i
            else:
                if maxd!=-1e10:
                    p.append(maxi)
                maxd = -1e10
                maxi = i
        return p
    def date2period(self,d): #时间映射到指定周期的x
        if self._period==15:
            for i in range(len(self._d)):
                if self._d[i][0]>=d:
                    return i
        return NaN
class StockOrder:
    """
    管理一个股票列表,(0 code,1 label,2 oder data,3 color,...)
    """
    IT2P = 0 #百分比
    IT2E9 = 1 #亿
    def __init__(self,npt):
        self._ls = []
        self._pagei = 0
        self._pagen = 1
        self._it2 = StockOrder.IT2P
        self._npt = npt
        self._needrender = False
    def update(self,ls,pagei,pagen,it2):
        self._ls = ls
        self._pagei = pagei
        self._pagen = pagen
        self._it2 = it2
        self._needrender = True
    def render(self,canvas,x,y,w,h,_class):
        #绘制背景
        canvas.beginPath()
        canvas.fillColor(Themos.BG_COLOR)
        canvas.rect(0,0,w,h)
        canvas.fill()        
        yy = y
        canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_MIDDLE)
        canvas.fontFace("zh")
        canvas.fontSize(Themos.ORDER_FONTSIZE)
        if _class==0:
            kn = 'hot'
        elif _class==1:
            kn = 'gn_hot'
        elif _class==2:
            kn = 'hy_hot'
        else:
            kn = ''
        hotcodes = stock.getHoldStocks(kn)
        for i in range(len(self._ls)):
            it = self._ls[i]
            if yy-y<h:
                if it[0] in self._npt.code2i:
                    ii = self._npt.code2i[it[0]]
                    """
                    1 5分钟均线向上发散买入提示，2 5分钟均线向下发散卖出提示
                    """
                    if ii in self._npt._warnings:
                        wa = self._npt._warnings[ii]
                        ma5 = wa[4][0]
                        ma10 = wa[4][1]
                        ma20 = wa[4][2]
                        ma30 = wa[4][3]
                        if wa[0]==HotPlotApp.BUYWARNING:
                            cc = Themos.WARN_BUY_COLOR
                            if ma5[-1]>ma5[-2] and ma10[-1]>ma10[-2] and ma20[-1]>ma20[-2]: #所有均线均向上
                                cc = Themos.WARN_BUY_COLOR2
                        elif wa[0]==HotPlotApp.SELLWARNING:
                            cc = Themos.WARN_SELL_COLOR
                            if ma5[-1]<ma5[-2] and ma10[-1]<ma10[-2] and ma20[-1]<ma20[-2]: #所有均线均向下
                                cc = Themos.WARN_SELL_COLOR2
                        elif wa[0]==HotPlotApp.NEWHIGHWARNING:
                            cc = Themos.WARN_NEWHIGH_COLOR
                        else:
                            cc = Themos.BGCOLOR
                        canvas.beginPath()
                        canvas.fillColor(cc)
                        canvas.rect(x,yy,64,Themos.ORDER_ITEM_HEIGHT)
                        canvas.fill()
                    """
                    1 日线boll通道上轨中轨向上 2 都向上 3 下轨向上
                    """
                    if ii < len(self._npt._BOLL):
                        bo = self._npt._BOLL[ii]
                        #rise = bo[-1,1]>=bo[-2,1] and bo[-1,2]>=bo[-2,2]#仅仅对通道上行的进行报警
                        rise = isrise(bo[-5:,1]) #and isrise(bo[-5:,2])
                        if rise and isrise(bo[-5:,0]):
                            cc = Themos.CAN_BUY_TEXTCOLOR2  #紫色
                        elif rise:
                            cc = Themos.CAN_BUY_TEXTCOLOR   #红色                      
                        elif bo[-1,0]>=bo[-2,0]: #下轨向上
                            cc = Themos.CAN_BUY_TEXTCOLOR3  #棕色
                        else:
                            cc = Themos.ORDER_BGCOLOR
                        canvas.beginPath()
                        canvas.fillColor(cc)
                        canvas.rect(x+64,yy,Themos.ORDER_WIDTH-64-5,Themos.ORDER_ITEM_HEIGHT)
                        canvas.fill()        
                    """
                    1 最近5个交易日早盘有上涨提示 2 最近5个交易日早盘有下跌提示
                    """
                    if ii in self._npt._zp and self._npt._zp[ii] is not None:
                        if self._npt._zp[ii][0]>0:
                            cc = Themos.RED_COLOR
                        else:
                            cc = Themos.GREEN_COLOR
                        canvas.beginPath()
                        canvas.fillColor(cc)
                        canvas.rect(x-5+Themos.ORDER_WIDTH,yy,5,Themos.ORDER_ITEM_HEIGHT)
                        canvas.fill()
                if self._npt._RSI[ii][-1]<30:
                    canvas.fillColor(Themos.ORDER_TEXTCOLOR2)
                    canvas.fontFace('zhb')
                elif self._npt._RSI[ii][-1]>80:
                    canvas.fillColor(Themos.ORDER_TEXTCOLOR3)
                    canvas.fontFace('zhb')
                else:
                    canvas.fillColor(Themos.ORDER_TEXTCOLOR)
                    canvas.fontFace("zh")
                canvas.text(x+64,yy+Themos.ORDER_ITEM_HEIGHT/2,it[1])
                
                #绘制涨跌幅
                canvas.fillColor(Themos.RED_COLOR if it[2]>0 else Themos.GREEN_COLOR)
                if self._it2==StockOrder.IT2P:
                    canvas.text(x+8,yy+Themos.ORDER_ITEM_HEIGHT/2,"%.02f%%"%it[2])
                elif self._it2==StockOrder.IT2E9:
                    v = abs(it[2])
                    if v>1e8:
                        s = "%.01f亿"%(it[2]/1e8)
                    elif v>1e7:
                        s = "%.01f千万"%(it[2]/1e7)
                    elif v>1e4:
                        s = "%d万"%int(it[2]/1e4)
                    else:
                        s = "%s"%str(it[2])
                    canvas.text(x+8,yy+Themos.ORDER_ITEM_HEIGHT/2,s)
            else:
                break
            yy+=Themos.ORDER_ITEM_HEIGHT
        #绘制选择区域
        canvas.beginPath()
        canvas.strokeColor(Themos.ORDER_SELCOLOR)
        canvas.strokeWidth(4)
        xx = x+1
        yy = y+self._pagei*self._pagen*Themos.ORDER_ITEM_HEIGHT
        canvas.moveTo(xx,yy)
        canvas.lineTo(xx,yy+self._pagen*Themos.ORDER_ITEM_HEIGHT)
        #canvas.rect(x+1,y+self._pagei*self._pagen*Themos.ORDER_ITEM_HEIGHT,Themos.ORDER_WIDTH,self._pagen*Themos.ORDER_ITEM_HEIGHT)
        canvas.stroke()
        self._needrender = False
class DateLabel:
    """
    显示一个日期包括时间
    """
    TEXTCOLOR = vg.nvgRGB(255,255,255)
    TEXTBGCOLOR = vg.nvgRGB(0,0,0)
    SIZE = 14
    def __init__(self):
        pass
    def render(self,canvas,x,y,w,h):
        canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_MIDDLE)
        canvas.beginPath()
        t = datetime.today()
        canvas.fillColor(DateLabel.TEXTBGCOLOR)
        canvas.fontFace("zh")
        canvas.fontBlur(5)
        canvas.fontSize(DateLabel.SIZE)
        canvas.fontBlur(0)
        canvas.text(x+w/2,y+h/2,stock.timeString2(t))
        canvas.fillColor(DateLabel.TEXTCOLOR)
        canvas.text(x+w/2,y+h/2,stock.timeString2(t))
        
class HotPlotApp(frame.app):
    """
    热键:
    Ctrl+F1 帮助
    F1 ETF F2 概念 F3 行业 F4 大盘 F5 持有 F6 关注 F7 昨日排行 F8 前天排行 F9 个股 F10 活跃
    NumPad 0 排行切换 日涨幅排行
    NumPad . 主力流入排行，1分钟流入排行 (仅适用于 ETF,概念,行业,个股)
    Ctrl+1,4,6,8股同屏  PageDown PageUp翻页 Home首页 End尾页 ,INSERT 反转排序
    NumPad 1,2,3,4,5,6 当天屏幕上的网格位置对应的股票切换到K线图模式
    Ctrl+(NumPad 1,2,3,4,5,6) 如果不在持有模式就是添加个股到持有，如果在持有模式就是删除
    Alt +(NumPad 1,2,3,4,5,6) 如果不在关注模式就是添加个股到关注，如果在关注模式就是删除
    a-z 0-9 输入拼音首字母过滤, 最后如果加空格表示可以在中间搜索,例如 消费电子 'dz '
    escape 清除过滤，取消k线模式
    NumPad / 看早盘的5秒图
    NumPad 7 看通道简图
    NumPad 9 切换时序 5,15,30,60,'d'
    NumPad 8 流入，成交量，量比，切换
    Left,Right 平移K线图表
    Up,Down 缩放K线图表
    """
    RT = 0
    BULLWAY = 1
    ZEROCOLOR = (0.9,0.9,0.9)
    REDCOLOR = (1,0,0)
    GREENCOLOR = (0,1,0)    
    companys = xueqiu.get_company_select()
    code2i = xueqiu.get_company_code2i()
    code2com = xueqiu.get_company_code2com()
    MAP2NUM = {
        sdl2.SDLK_KP_4:0,sdl2.SDLK_KP_5:1,sdl2.SDLK_KP_6:2,sdl2.SDLK_KP_1:3,sdl2.SDLK_KP_2:4,sdl2.SDLK_KP_3:5
    }
    CLASS = ['ETF','概念','行业','大盘','持有','关注','昨日排行','前天排行','个股','活跃','ETF热点','概念热点','行业热点']
    ORDER = ['日涨幅','主力流入','1分钟流入','1分钟涨速']
    NONEWARNING = 0
    BUYWARNING = 1
    SELLWARNING = 2
    NEWHIGHWARNING = 3
    def __init__(self,title,w,h):
        super(HotPlotApp,self).__init__(title,w,h)
        self._numsub = (3,2) #同屏数量 1 (1,1),4 (2,2),6 (3,2)
        self._oldnumsub = self._numsub
        self._oldpagen = 0
        self._SO = StockOrder(self)
        self._SPV = [StockPlot() for i in range(10)]
        self._prefix = ('2',) #选择分类
        self._flowin = False #净流入
        self._hasboll = False #有通道
        self._reverse = False #排序
        self._em933 = False 
        self._pagen = 0 #页面
        self._topn = 64
        self._class = 0
        self._order = 0 #排序方式
        self._current = None
        self._help = False
        self._helpimg = None
        self._filter = ''
        self._kwidth = 10 #k线宽度
        self._kei = 0
        self._period = 'd'
        self._volmode = StockPlot.FLOW
        self._kmode = HotPlotApp.RT
        self._K = None
        self._D = None   
        self._Data = None   
        self._rtk = 0 #0 rt 1 k
        self._messagebox = None
        self.setClearColor(Themos.BG_COLOR)
        self._ltt = datetime.today()
        self._lut = self._ltt
        self._needUpdate = False
        threading.Thread(target=self.update_data_loop).start()
        self._BOLL = []
        self._RSI = []
        self._warnings = None
        self._zp = {}
        self._msl = {}
        self._mslb = False
        self._warningbox = []
        self._warningbox_isopen = False
        self._bollfilter = 0 #0 不过滤,1 向上 , 2 向下
        self.updateTitle()
        self.createFrame(0,0,Themos.ORDER_WIDTH,self._h,'list')
        self.createFrame(Themos.ORDER_WIDTH,self.CAPTION_HEIGHT,self._w-Themos.ORDER_WIDTH,self._h-self.CAPTION_HEIGHT,'graph')
        self._readywav = self.loadWave('lobby_notification_matchready.wav') #测试
        self._buywav = self.loadWave('dropzone_select.wav')
        self._sellwav = self.loadWave('playerping.wav')
        self._newhighwav = self.loadWave('cashreg.wav')
        self._cancelwav = self.loadWave('money_collect_05.wav')
        self._strongwav = self.loadWave('heartbeatloop.wav')
        self._strongsellwav = self.loadWave('rocketalarm.wav')
        self.setMixVolume(-1,0.1)
        self.playWave(0,self._readywav)
    def update60(self):
        """
        一个小时更新一次,这包括日BOLL,CCI(标准化到0-100),RSI
        """
        self._K240,self._D240 = xueqiu.get_period_k(240)
        self._MA30 = stock.maMatrix(self._K240,30)
        BOLL = []
        RSI = []
        for i in range(self._K240.shape[0]):
             BOLL.append(stock.boll(self._K240[i,:]))
             RSI.append(stock.rsi(self._K240[i,:],6))
        self._BOLL = BOLL
        self._RSI = RSI

    def update_data_loop(self):
        #一次性加载日线数据
        t60 = datetime.today()
        self.update60()
        n = 0
        while self._running:
            if n>10:
                b,t = shared.fromRedis('runtime_update')
                if self._Data is None or (b and t!=self._lut):
                    self._lut = t
                    print("update %s"%t)
                    k,d,e = xueqiu.get_rt(4) #取得最近3天的1分钟数据(0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting)
                    k15,d15 = xueqiu.get_period_k(15)
                    for i in range(k15.shape[0]): #处理价格为0的情况
                        if k15[i,0]==0:
                            for j in range(k15.shape[1]):
                                if k15[i,j]!=0:
                                    k15[i,:j] = k15[i,j]
                                    break
                            continue
                    self._Data = (k,d,k15,d15,[],e)
                    #做买入和卖出预警
                    self.watchDog()
                    self.updatedata()
            if self._needUpdate: #每分钟更新一次
                if stock.isTransDay() and stock.isTransTime() and datetime.today().hour!=t60.hour:
                    self.update60()
                    t60 = datetime.today()
                self.updatedata()
                self._needUpdate = False
            sdl2.SDL_Delay(10)
            n+=1
    def watchDog(self):
        old = self._warnings
        self._warnings = {}
        k5,d5 = xueqiu.get_period_k(5)
        rtk = self._Data[0]
        for i in range(len(HotPlotApp.companys)):
            bo = self._BOLL[i]
            #rise = bo[-1,1]>=bo[-2,1] and bo[-1,2]>=bo[-2,2]#仅仅对通道上行的进行报警
            rise = True
            if rise:
                #监视上升趋势中的5分钟空头排列和5分钟多头排列
                ma5 = stock.ma(k5[i],5)
                ma10 = stock.ma(k5[i],10)
                ma20 = stock.ma(k5[i],20)
                ma30 = stock.ma(k5[i],30)
                if ma5[-1]>ma10[-1] and ma10[-1]>ma20[-1] and ma20[-1]>ma30[-1]: #均线多头
                    F = rtk[i,:,3]+rtk[i,:,4]
                    F[F!=F]=0 #消除NaN
                    m0 = stock.ma(F,5)
                    m1 = stock.ma(F,30)
                    self._warnings[i] = (HotPlotApp.BUYWARNING,np.argmax(k5[i])==len(d5)-1,0,0,(ma5,ma10,ma20,ma30),(m0,m1),HotPlotApp.companys[i])#0多头,1监视5个交易日新高,2价格打开，3主力流入打开，4均线，5主力均线
                elif ma30[-1]>ma20[-1] and ma20[-1]>ma10[-1] and  ma10[-1]>ma5[-1]: #均线空头
                    F = rtk[i,:,3]+rtk[i,:,4]
                    F[F!=F]=0 #消除NaN
                    m0 = stock.ma(F,5)
                    m1 = stock.ma(F,30)                    
                    self._warnings[i] = (HotPlotApp.SELLWARNING,False,0,0,(ma5,ma10,ma20,ma30),(m0,m1),HotPlotApp.companys[i])
        if old is not None:
            nc = 0
            for i in range(len(HotPlotApp.companys)):
                if HotPlotApp.companys[i][3]==self._prefix[0]:# or HotPlotApp.companys[i][3]=='0' or HotPlotApp.companys[i][3]=='1':#仅仅警告ETF和个股
                    ob = i in old
                    nb = i in self._warnings
                    if not ob and nb:
                        if self._warnings[i][0]==HotPlotApp.BUYWARNING:
                            if self.warning('+',i,self._warnings[i]):
                                self.playWave(nc,self._buywav) #多头买入
                                nc+=1
                        elif self._warnings[i][0]==HotPlotApp.SELLWARNING:
                            if self.warning('+',i,self._warnings[i]):
                                self.playWave(nc,self._sellwav) #空头卖出
                                nc+=1
                    elif ob and not nb:
                        if self.warning('-',i,old[i]):
                            self.playWave(nc,self._cancelwav) #特征不稳定，又消失了
                            nc+=1
                    elif ob and nb:
                        if self._warnings[i][0]==HotPlotApp.BUYWARNING and not ismafashan(old[i][4]) and ismafashan(self._warnings[i][4]): #强化提示
                            if self.warning('++',i,self._warnings[i]):
                                self.playWave(nc,self._strongwav,2)
                                nc+=1
                        elif self._warnings[i][0]==HotPlotApp.SELLWARNING and not ismafashan(old[i][4]) and ismafashan(self._warnings[i][4]): #强化提示
                            if self.warning('--',i,self._warnings[i]):
                                self.playWave(nc,self._strongsellwav)
                                nc+=1
        """
        对最近的早盘进行分析，如果早盘1小时最大跌幅在最近5个交易日较大-1,反之+1
        """
        for i in range(len(HotPlotApp.companys)):
            if HotPlotApp.companys[i][3]==self._prefix[0]:
                self._zp[i] = zpfx(k5[i],d5)
                #print(HotPlotApp.companys[i],self._zp[i])
                
    def warning(self,typ,i,warning):
        """
        加入一个警报，最近5分钟没发生过此类警报
        """
        t = datetime.today()
        dt = timedelta(seconds=5*60)
        for j in range(len(self._warningbox)-1,0,-1):
            if self._warningbox[j][2]==j and self._warningbox[j][0]==typ and t-self._warningbox[j][3]<=dt:
                return False
            if t-self._warningbox[j][3]>dt:
                break
        self._warningbox.append((typ,warning,i,datetime.today()))
        return True
    def getCurrentRT(self):
        return self._Data
    def onLoop(self,t,dt):
        tt = datetime.today()
        if tt.second!=self._ltt.second:
            self._ltt = tt
            self.updateTitle()
        self.renderfbo()
    def updateTitle(self):
        tt = datetime.today()
        if self._messagebox:
            title = "%s %s %d月%d日 %02d:%02d:%02d %s %s"%(HotPlotApp.CLASS[self._class],HotPlotApp.ORDER[self._order],tt.month,tt.day,tt.hour,tt.minute,tt.second,self._filter.upper(),self._messagebox)
        else:
            title = "%s %s %d月%d日 %02d:%02d:%02d %s"%(HotPlotApp.CLASS[self._class],HotPlotApp.ORDER[self._order],tt.month,tt.day,tt.hour,tt.minute,tt.second,self._filter.upper())
        self.setWindowTitle(title)
    def renderfbo(self):
        try:
            if self._SO._needrender:
                canvas,w,h = self.beginFrame('list')
                self._SO.render(canvas,0,0,w,h,self._class)
                self.endFrame()
            needrender = False
            for spv in self._SPV:
                if spv._needrender:
                    needrender = True
                    break
            if needrender:
                canvas,w,h = self.beginFrame('graph')
                x = 0
                y = 0          
                col = self._numsub[0]
                raw = self._numsub[1]
                dw = int(w/col)
                dh = int((h-Themos.XLABELHEIGHT)/raw)
                scale = scale=w/(720*self._numsub[0])
                if scale<1:
                    scale=1
                if scale>1.6:
                    scale=1.6
                for xi in range(col):
                    for yi in range(raw):
                        self._SPV[yi*col+xi].render(canvas,x+xi*dw,y+yi*dh,dw,dh,xaxis=yi==raw-1,scale=scale,warnings=self._warnings)
                self.endFrame()
        except Exception as e:
            mylog.printe(e)
            log.error("render "+str(e))
    def render(self,canvas,x,y,w,h):
        if 'spv' in self._msl:
            canvas.beginPath()
            canvas.strokeColor(Themos.CROSS_COLOR)
            canvas.strokeWidth(1)
            canvas.moveTo(self._msl['mx'],self._msl['y'])
            canvas.lineTo(self._msl['mx'],self._msl['y']+self._msl['h'])
            canvas.moveTo(self._msl['x']+Themos.YLABELWIDTH,self._msl['my'])
            canvas.lineTo(self._msl['x']+self._msl['w'],self._msl['my'])
            canvas.stroke()
            if self._msl['xlabel'] is not None:
                canvas.fontFace('zh')
                canvas.fontSize(14)
                canvas.fillColor(Themos.TEXTCOLOR)
                if self._msl['mx']<self._msl['x']+self._msl['w']/2:
                    canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_BOTTOM)
                else:
                    canvas.textAlign(vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_BOTTOM)
                canvas.text(self._msl['mx'],self._msl['y']+self._msl['h']-2,self._msl['xlabel'])
            if self._msl['ylabel'] is not None:
                canvas.fontFace('zh')
                canvas.fontSize(14)
                canvas.fillColor(Themos.TEXTCOLOR)
                canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_BOTTOM)
                canvas.text(self._msl['x']+Themos.YLABELWIDTH,self._msl['my'],self._msl['ylabel'])
            if self._msl['k'] is not None:
                canvas.fontFace('zhb')
                canvas.fontSize(14)
                if self._msl['mx']<self._msl['x']+self._msl['w']/2:
                    canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_BOTTOM)
                else:
                    canvas.textAlign(vg.NVG_ALIGN_RIGHT|vg.NVG_ALIGN_BOTTOM)                
                mx = self._msl['mx']
                my = self._msl['my']
                k = self._msl['k']
                tx = ['开','高','低','收']
                for i in range(1,5):
                    canvas.fillColor(Themos.RED_COLOR if k[i]>0 else Themos.GREEN_COLOR)
                    canvas.text(mx,my,"%s %.2f%%"%(tx[i-1],k[i]))
                    my+=20
            
    def messagebox(self,msg):
        self._messagebox = msg
        self.updateTitle()
        #self.delayUpdate()
    def getGrowColor(self,r): #根据涨幅返回颜色tuple
        r = r/3
        if r>1:
            r = 1
        if r<-1:
            r = -1
        if r>0:
            return f2color255(intercolor(HotPlotApp.ZEROCOLOR,HotPlotApp.REDCOLOR,r))
        else:
            return f2color255(intercolor(HotPlotApp.ZEROCOLOR,HotPlotApp.GREENCOLOR,-r))
    def updatedata(self):
        try:
            self.updatedata_imp()
        except Exception as e:
            mylog.printe(e)
            log.error("updatedata "+str(e))
    def updatedata_imp(self):
        if (self._class>=0 and self._class<3) or self._class==8:
            tops = self.riseTop(self._topn)
        elif self._class==3: #大盘
            tops = self.mapCode2DataSource(['SH000001','SZ399001','SZ399006','SH000688'])
        elif self._class==4: #持有
            tops = self.mapCode2DataSource(stock.getHoldStocks())
        elif self._class==5: #关注
            tops = self.mapCode2DataSource(self.getFav())
        elif self._class==6: #昨日
            tops = self.mapCode2DataSource(self.getYesterdayTop(1))
        elif self._class==7: #前天
            tops = self.mapCode2DataSource(self.getYesterdayTop(2))  
        elif self._class==9: #最近活跃               
            tops = self.mapCode2DataSource(self.activeTop())
        elif self._class==10: #ETF热点
            tops = self.mapCode2DataSource(stock.getHoldStocks(name='hot'))
        elif self._class==11: #概念热点
            tops = self.mapCode2DataSource(stock.getHoldStocks(name='gn_hot'))
        elif self._class==12: #行业热点
            tops = self.mapCode2DataSource(stock.getHoldStocks(name='hy_hot'))                    
        R = []
        TOPS = []
        if len(self._filter)==0:
            for it in tops:
                R.append((it[0][1],it[0][2],it[1],None))
                TOPS.append(it)            
        else:
            F = self._filter.upper()
            i = F.find(' ')
            if i>0:
                F = F[:i]
            for it in tops:
                pyh = pinyinhead(it[0][2])
                j = pyh.find(F)
                if (i<0 and j==0) or (i>0 and j>0):
                    R.append((it[0][1],it[0][2],it[1],None))
                    TOPS.append(it)
        NS = self._numsub
        PageNum = NS[0]*NS[1]
        if self._pagen*PageNum>=len(TOPS):
            a = len(TOPS)/PageNum
            self._pagen = math.floor(a)
            if a==math.floor(a) and PageNum!=1:
                self._pagen -=1
        if self._pagen<0:
            self._pagen = 0
        self._SO.update(R,self._pagen,PageNum,StockOrder.IT2P if self._order==0 or self._order==3 else StockOrder.IT2E9)
        if self._period!=15 and self._kmode==HotPlotApp.BULLWAY:
            K,D = xueqiu.get_period_k(240 if self._period=='d' else self._period)
        ww = (self._w-Themos.ORDER_WIDTH)/NS[0] #视口宽度
        for i in range(NS[0]*NS[1]):
            j = self._pagen*PageNum+i
            self._SPV[i].clear()
            if j<len(TOPS):
                it = TOPS[j]
                k = it[2] 
                for s in range(1,len(k)):#处理价格为零的情况
                    if k[s,0]==0:
                        k[s,0] = k[s-1,0]
                if self._rtk==1 or (self._current is not None and i==self._current):
                    title = "%s %s %s"%(it[0][2],it[0][1],"%d分钟"%self._period if type(self._period)==int else "日线")
                    self._SPV[i].viewMode(vm=self._volmode)
                    self._kei = self._SPV[i].updateK(it[0][1],title,self._period,int(ww/self._kwidth),self._kei,item=it)
                else:
                    if self._kmode==HotPlotApp.RT:
                        self._SPV[i].viewMode(vm=self._volmode)
                        K,D = it[2],it[3]
                        isem933 = False
                        title = "%s %s"%(it[0][2],it[0][1])
                        if self._em933:
                            b,k933,d933 = self.getem33flow(it[0][1])
                            if b:
                                isem933 = True
                                K,D = self.em933(k933,d933)
                        if isem933:
                            rtk = it[2][:,0]
                            rtd = it[3]
                            for s in range(len(rtd)-1,1,-1):
                                if rtd[s].hour==9 and rtd[s].minute<=30:
                                    rtk = rtk[:s]
                                    if len(rtk)<=60: #太短
                                        rtk = None
                                    break
                            self._SPV[i].update(it[0][1],title,K,D,isem933=True,ma60b=rtk,item=it)
                        else:
                            self._SPV[i].update(it[0][1],title,K,D,ma5b=self.getma5b(it[4],it[5]),item=it)
                    elif self._kmode==HotPlotApp.BULLWAY:
                        if self._period==15:
                            k = it[4]
                            d = it[5]
                        else:
                            if it[0][1] in HotPlotApp.code2i:
                                s = HotPlotApp.code2i[it[0][1]]
                                k = K[s]
                                d = D
                            else:
                                k = []
                                d = []
                        title = "%s %s"%(it[0][2],"%d分钟"%self._period if type(self._period)==int else "日线")
                        self._SPV[i].updateBollWay(it[0][1],title,k,d,self._period)
            else:
                self._SPV[i]._needrender = True

    def em933(self,K,D): #补全，使得长度固定为30分钟
        d = []
        for i in range(len(D)):
            d.append(D[i])
        while d[-1].hour==9:
            d.append(d[-1]+timedelta(seconds=5))
        k = np.empty((len(d),K.shape[1]))
        k[:K.shape[0],:] = K[:,:]
        if len(d)>len(D):
            k[K.shape[0]:,:] = NaN#NaN Plot将不显示
        return k,d
    def getem33flow(self,code):
        k,d,K,D,bolls,em = self.getCurrentRT()
        if em is not None:
            a,ts,emcode2i = em
            if code in emcode2i:
                i = emcode2i[code]
                return True,a[i,:],ts
        return False,None,None
    def keyDown(self,event):
        mod = event.key.keysym.mod
        sym = event.key.keysym.sym
        self._messagebox = None
        if sym==sdl2.SDLK_F1: #ETF
            if mod&sdl2.KMOD_CTRL: #ctrl+F1帮助
                #self._help = True
                self._class = 10
            else:
                if self._class==3:
                    self._numsub = self._oldnumsub
                self._class = 0
                self._prefix=('2',)
            self._current = None
        elif sym==sdl2.SDLK_F2: #概念
            if mod&sdl2.KMOD_CTRL:
                self._class = 11 #概念热点
            else:
                if self._class==3:
                    self._numsub = self._oldnumsub
                self._class = 1
                self._prefix=('91',)
            self._current = None
        elif sym==sdl2.SDLK_F3: #行业
            if mod&sdl2.KMOD_CTRL:
                self._class = 12 #行业热点
            else:
                if self._class==3:
                    self._numsub = self._oldnumsub
                self._class = 2
                self._prefix=('90',)
            self._current = None
        elif sym==sdl2.SDLK_F4: #大盘
            self._class = 3
            self._current = None
            self._oldnumsub = self._numsub
            self._numsub = (2,2)
            self._prefix=('90',)
        elif sym==sdl2.SDLK_F5: #持有
            self._class = 4
            self._current = None
        elif sym==sdl2.SDLK_F6: #关注
            self._class = 5
            self._current = None
        elif sym==sdl2.SDLK_F7: #昨日排行
            self._class = 6
            self._current = None
        elif sym==sdl2.SDLK_F8: #前天排行
            self._class = 7
            self._current = None
        elif sym==sdl2.SDLK_F9: #个股
            if self._class==3:
                self._numsub = self._oldnumsub            
            self._class = 8
            self._current = None
            self._prefix=('1','0')
        elif sym==sdl2.SDLK_F10: #活跃的
            if self._class==3:
                self._numsub = self._oldnumsub              
            self._class = 9
            self._current = None
        elif mod&sdl2.KMOD_CTRL and sym==sdl2.SDLK_1: #单个窗口
            self._numsub = (1,1)
            self._current = None
        elif mod&sdl2.KMOD_CTRL and sym==sdl2.SDLK_4: #单个窗口
            self._numsub = (2,2)
            self._current = None
        elif mod&sdl2.KMOD_CTRL and sym==sdl2.SDLK_6: #单个窗口
            self._numsub = (3,2)
            self._current = None
        elif mod&sdl2.KMOD_CTRL and sym==sdl2.SDLK_8: #单个窗口
            self._numsub = (4,2)
            self._current = None
        elif sym==sdl2.SDLK_PAGEUP:
            self._kei = 0
            self._pagen-=1
        elif sym==sdl2.SDLK_PAGEDOWN:
            self._kei = 0
            self._pagen+=1
        elif sym==sdl2.SDLK_HOME:
            self._kei = 0
            self._pagen = 0
        elif sym==sdl2.SDLK_END:
            self._kei = 0
            self._pagen = 1e10
        elif sym==sdl2.SDLK_INSERT: #反转排序
            self._kei = 0
            self._reverse = not self._reverse
        elif sym==sdl2.SDLK_LEFT:
            knum = (self._w-Themos.ORDER_WIDTH)/(self._kwidth*self._numsub[0])
            self._kei += int(knum/2)
        elif sym==sdl2.SDLK_RIGHT:
            knum = (self._w-Themos.ORDER_WIDTH)/(self._kwidth*self._numsub[0])
            self._kei -= int(knum/4)
            if self._kei<0:
                self._kei = 0            
        elif sym==sdl2.SDLK_UP:
            self._kwidth += 1
            if self._kwidth>20:
                self._kwidth = 20          
        elif sym==sdl2.SDLK_DOWN:
            self._kwidth -= 1
            if self._kwidth<8:
                self._kwidth = 8
        elif sym==sdl2.SDLK_KP_9: #k线模式，切换周期
            p = {5:0,15:1,30:2,60:3,'d':4}
            pp = [5,15,30,60,'d']
            i = p[self._period]+1
            self._period = pp[i] if i<=4 else pp[0]
            self.messagebox("切换到%s周期"%(p[self._period]))
        elif sym==sdl2.SDLK_KP_MULTIPLY: #k线模式，切换boll 和 ma
            StockPlot.KVMODE = 1 if StockPlot.KVMODE==0 else 0
            self.messagebox("%s"%('均线显示' if StockPlot.KVMODE==1 else 'BOLL显示'))
        elif sym==sdl2.SDLK_KP_DIVIDE: #切换早盘的密集显示模式
            self._em933 = not self._em933
            self.messagebox("%s"%('早盘快速更新' if self._em933 else '关闭快速更新'))
        elif sym==sdl2.SDLK_KP_8:
            if self._volmode==StockPlot.FLOW:
                self._volmode = StockPlot.VOL
            elif self._volmode==StockPlot.VOL:
                self._volmode = StockPlot.LMR
            else:
                self._volmode = StockPlot.FLOW
            if self._rtk == 0:
                msg = {StockPlot.FLOW:"FLOW",StockPlot.VOL:"成交量",StockPlot.LMR:"量比"}[self._volmode]
            else:
                msg = {StockPlot.FLOW:"FLOW",StockPlot.VOL:"MACD",StockPlot.LMR:"RSI"}[self._volmode]
            self.messagebox(msg)
        elif sym==sdl2.SDLK_KP_7:
            if self._kmode==HotPlotApp.RT:#切换实时图和15分钟通道图和早盘实时图
                self._kmode=HotPlotApp.BULLWAY
            else:
                self._kmode=HotPlotApp.RT
        elif sym==sdl2.SDLK_KP_0: #切换排序
            self._order+=1
            if self._order>1:
                self._order = 0
            self.messagebox("成交量排序" if self._order==1 else "涨幅排序")
        elif sym==sdl2.SDLK_KP_PERIOD:
            self._order+=1
            if self._order<2:
                self._order = 2
            elif self._order>3:
                self._order = 2
        elif sym==sdl2.SDLK_TAB:
            self._warningbox_isopen = not self._warningbox_isopen
        elif sym==sdl2.SDLK_KP_PLUS:
            self._bollfilter = 1 if self._bollfilter!=1 else 0
            self.messagebox("%s"%('仅显示通道向上的' if self._bollfilter==1 else '关闭过滤'))
        elif sym==sdl2.SDLK_KP_MINUS:
            self._bollfilter = 2 if self._bollfilter!=2 else 0
            self.messagebox("%s"%('仅显示通道向下的' if self._bollfilter==2 else '关闭过滤'))
        elif sym==sdl2.SDLK_KP_ENTER:
            self._rtk = 1 if self._rtk==0 else 0
            if self._rtk==0:
                self._volmode = StockPlot.FLOW
            else:
                 self._volmode = StockPlot.LMR
        elif sym in HotPlotApp.MAP2NUM:
            oldcurrent = self._current
            if (self._numsub[0]==3 and self._numsub[1]==2) or self._numsub[0]==1:
                self._current = HotPlotApp.MAP2NUM[sym]
            elif self._numsub[0]==4 and self._numsub[1]==2:
                self._current = HotPlotApp.MAP2NUM[sym]
                if self._current>=3:
                    self._current+=1
            elif self._numsub[0]==2 and self._numsub[1]==2:
                self._current = HotPlotApp.MAP2NUM[sym]
                if self._current>1:
                    self._current-=1            
            if mod&sdl2.KMOD_RCTRL and self._class!=4:#增加持有
                code = self._SPV[self._current]._code
                name = HotPlotApp.code2com[code][2]
                self.messagebox("增加持有:%s"%(name))
                stock.holdStock(code,True)
                self._current = None
            if mod&sdl2.KMOD_RCTRL and self._class==4:#删除持有
                code = self._SPV[self._current]._code
                name = HotPlotApp.code2com[code][2]
                self.messagebox("删除持有:%s"%(name))
                stock.holdStock(code,False)
                self._current = None
            while mod&sdl2.KMOD_LCTRL:#增加HOT
                if self._class==0:
                    kname = 'hot'
                elif self._class==1:
                    kname = 'gn_hot'
                elif self._class==2:
                    kname = 'hy_hot'
                else:
                    break
                code = self._SPV[self._current]._code
                name = HotPlotApp.code2com[code][2]
                self.messagebox("增加HOT:%s"%(name))
                stock.holdStock(code,True,name=kname)
                self._current = None
                break
            while mod&sdl2.KMOD_LCTRL:#删除HOT
                if self._class==10:
                    kname = 'hot'
                elif self._class==11:
                    kname = 'gn_hot'
                elif self._class==12:
                    kname = 'hy_hot'
                else:
                    break
                code = self._SPV[self._current]._code
                name = HotPlotApp.code2com[code][2]
                self.messagebox("删除HOT:%s"%(name))
                stock.holdStock(code,False,name=kname)
                self._current = None
                break      
            if mod&sdl2.KMOD_RSHIFT and self._class!=3:#增加关注
                code = self._SPV[self._current]._code
                name = HotPlotApp.code2com[code][2]
                stock.execute("insert into notebook (date,code,name,context,note) values ('%s','%s','%s','%s','%s')"%(stock.dateString(date.today()),code,name,'HotPlotApp',''))
                self._current = None
                self.messagebox("增加关注:%s"%(name))
            if mod&sdl2.KMOD_RSHIFT and self._class==3:#删除关注
                code = self._SPV[self._current]._code
                name = HotPlotApp.code2com[code][2]
                self.messagebox("删除关注:%s"%(name))
                stock.execute("delete from notebook where date='%s' and code='%s'"%(stock.dateString(date.today()),code))
                self._current = None
            else:
                self._kei = 0
                if oldcurrent==self._current:
                    self._current = None
        elif sym==sdl2.SDLK_ESCAPE:
            self._filter = ''
            self._numsub = self._oldnumsub
            self._pagen = self._oldpagen
            self._current = None
            self._help = False
        elif sym==sdl2.SDLK_BACKSPACE:
            if len(self._filter)>0:
                self._filter = self._filter[:-1]
        elif sym==sdl2.SDLK_RETURN:
            if self._numsub[0]==1:
                self._current = 0 if self._current is None else None
        elif (sym>=sdl2.SDLK_a and sym<=sdl2.SDLK_z) or (sym>=sdl2.SDLK_0 and sym<=sdl2.SDLK_9) or sym==sdl2.SDLK_SPACE:
            if self._filter=='':
                self._oldpagen = self._pagen
                self._oldnumsub = self._numsub
            self._current = None
            self._numsub = (1,1)
            self._pagen = 0
            self._filter+=chr(sym)
            self.setWindowTitle(self._filter)
        else:
            return

        self._needUpdate = True
    def getma5b(self,K15,D15,n=3):
        #f返回一个plotfs2 的ma5b需要的参数，用于绘制5日均线 n = 3起点位置在3天前
        if n==0:
            ma5b = K15[-16*n-16*5:].sum()/80
        else:
            ma5b = K15[-16*n-16*5:-16*n].sum()/80
        k15b = K15[-16*n-16*5:]
        return (ma5b,k15b)        
    def isSelected(self,company,bolls,k):
        def onif(b,s):
            return (b and s) or not b
        return company[3] in self._prefix and onif(self._flowin,k[-1,3]+k[-1,4]>0) and onif(self._hasboll,company[1] in bolls)      
    def it2order(self,i,k): #一个便利函数,更加_order选择要排序的项
        if self._order==0:
            order = k[i,-1,1] #日涨幅
        elif self._order==1:
            order = k[i,-1,3]+k[i,-1,4] #主力排序
        elif self._order==2:
            if k.shape[1]>1:
                order = (k[i,-1,3]+k[i,-1,4])-(k[i,-2,3]+k[i,-2,4]) #1分钟主力流入排序
            else:
                order = k[i,-1,3]+k[i,-1,4]
        elif self._order==3: #1分钟涨数榜
            if k.shape[1]>1:
                order = k[i,-1,1]-k[i,-2,1]
            else:
                order = k[i,-1,3]+k[i,-1,4]
        else:
            order = k[i,-1,1] #日涨幅
        return order
    def riseTop(self,top=18):
        """
        涨幅排行,满足大资金流入，5日均线上有强通道或者返回强通道中
        返回值 [(com,price,hug,rang,k,d,ma5b),...]
        """
        k,d,K,D,bolls,em = self.getCurrentRT()
        companys = HotPlotApp.companys
        R = []
        for i in range(len(companys)):
            if i<k.shape[0] and self.isSelected(companys[i],bolls,k[i]):
                bo = self._BOLL[i]
                rise = isrise(bo[-5:,1]) #and isrise(bo[-5:,2])
                if self._bollfilter==0 or (self._bollfilter==1 and rise) or (self._bollfilter==2 and not rise):
                    R.append((companys[i],self.it2order(i,k),k[i],d,K[i],D,bolls)) #0 company,1 涨幅(排序项) 2 k 3 d 4 K15 5 D15 6 bolls
        TOPS = sorted(R,key=lambda it:it[1],reverse=not self._reverse)
        #将三点指数追加在末尾
        return TOPS #[:top]            
    def mapCode2DataSource(self,codes,top=18):
        """
        将代码列表映射为数据源
        """
        k,d,K,D,bolls,em = self.getCurrentRT()
        companys = HotPlotApp.companys   
        R = []
        for code in codes:
            i = HotPlotApp.code2i[code]
            R.append((companys[i],self.it2order(i,k),k[i],d,K[i],D,bolls))
        return sorted(R,key=lambda it:it[1],reverse=not self._reverse) #R#[:top]
    def activeTop(self,top=18):
        """
        最近比较活跃的
        """
        tb = {'90':(5,3),"91":(20,4),"2":(5,3),"0":(10,3),"1":(10,3)}
        it = tb[self._prefix[0]]
        TOPS = monitor.get10Top(self._prefix[0],it[0],it[1],reverse=not self._reverse)
        return TOPS
    def getYesterdayTop(self,n=1,top=18):
        """
        返回昨日涨幅榜
        """
        k,d,k15,d15,bolls,em = self.getCurrentRT()
        companys = HotPlotApp.companys
        t = datetime.today()
        for i in range(len(d)-1,0,-1):
            if d[i].day!=t.day:
                if n==1:
                    break
                else:
                    n-=1
                    t = d[i]
        R = []
        if i>0:
            TOPS = []
            for j in range(len(companys)):
                if j<k.shape[0] and self.isSelected(companys[j],bolls,k[j,:i]):
                    R.append((companys[j][1],k[j,i,1]))
            TOPS = sorted(R,key=lambda it:it[1],reverse=not self._reverse)
            R = []
            for it in TOPS:
                R.append(it[0])
        return R[:top]  
    def getFav(self):
        """
        返回关注
        """
        today = date.today()  
        after = today-timedelta(days=20)
        result = stock.query("select * from notebook where date>='%s' order by date desc"%(stock.dateString(after)))
        S = {}
        for it in result:
            S[it[2]] = it
        return S.keys()
    def onMouseMotion(self,event):
        """
        显示数据细节
        """
        if self._mslb:
            mx = event.motion.x
            my = event.motion.y
            self._msl = {}
            if mx>Themos.ORDER_WIDTH:
                col = self._numsub[0]
                raw = self._numsub[1]
                (x,y,w,h,fbo,name) = self.getFrame("graph")
                dw = int(w/col)
                dh = int((h-Themos.XLABELHEIGHT)/raw)
                for xi in range(col):
                    for yi in range(raw):
                        spv = self._SPV[yi*col+xi]
                        if spv._k is not None and mx>x+xi*dw and mx<x+(xi+1)*dw and my>y+yi*dh and my<y+yi*dh+dh:
                            self._msl['spv'] = spv
                            self._msl['mx'] = mx
                            self._msl['my'] = my
                            self._msl['x'] = x+xi*dw
                            self._msl['y'] = y+yi*dh
                            self._msl['w'] = dw
                            self._msl['h'] = dh
                            self._msl['xlabel'] = None
                            self._msl['ylabel'] = None
                            self._msl['k'] = None

                            yy = my-self._msl['y']
                            iskplot = False
                            if spv._upmode==StockPlot.RT:
                                if yy<2*dh/3:
                                    self._msl['ylabel'] = "%.3f"%spv._kplot.wy2y(my-y)
                                else:
                                    self._msl['ylabel'] = "%.2e"%spv._vplot.wy2y(my-y)
                            elif spv._upmode==StockPlot.K:
                                if yy<dh/2:
                                    iskplot = True
                                    self._msl['ylabel'] = "%.3f"%spv._kplot.wy2y(my-y)
                                elif yy<dh/2+dh/4:
                                    self._msl['ylabel'] = "%.2e"%spv._vplot.wy2y(my-y)
                                else:
                                    self._msl['ylabel'] = "%.2f"%spv._fplot.wy2y(my-y)
                            elif spv._upmode==StockPlot.BOLLWAY:
                                pass

                            dx = 0.5*dw/len(spv._d)
                            ix = int(spv._kplot.wx2x(mx-x+dx))
                            if ix>=0 and ix<len(spv._d):
                                t = spv._d[ix]
                                if type(t)==tuple:
                                    if type(t[0])==date:
                                        self._msl['xlabel'] = stock.dateString(t[0])
                                    else:
                                        self._msl['xlabel'] = stock.timeString(t[0])
                                else:
                                    self._msl['xlabel'] = stock.timeString(t)
                                if iskplot and ix-1>=0 and len(spv._k.shape)>1 and spv._k.shape[1]==5:
                                    c = spv._k[ix-1][4]
                                    self._msl['k'] = (spv._k[ix]-c)*100/c                            
                            self.delayUpdate()
                            break
        super(HotPlotApp,self).onMouseMotion(event)
    def onMouseUp(self,event):
        if event.button.button==sdl2.SDL_BUTTON_LEFT:
            if event.button.x<Themos.ORDER_WIDTH:
                self._pagen = int(int(event.button.y/Themos.ORDER_ITEM_HEIGHT)/(self._numsub[0]*self._numsub[1]))
                self._needUpdate = True
            else:
                self._mslb = not self._mslb
                win32api.ShowCursor(not self._mslb)
                self._msl = {}
                self.delayUpdate()
        super(HotPlotApp,self).onMouseUp(event)
