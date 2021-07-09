from numpy.core.numeric import NaN
from sdl2.keycode import SDLK_LCTRL
from app.nanovg import frame,vg
from app import monitor,xueqiu,stock,shared,mylog
from pypinyin import pinyin, Style
from datetime import date,datetime,timedelta
import numpy as np
import threading
import math
import sdl2
from OpenGL import GL
import ctypes

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
class ThemosDefault:
    BGCOLOR = (0.95,0.95,0.95,1) #图表背景颜色

    MA60_COLOR = vg.nvgRGB(255,128,60) #ma60颜色
    PRICE_COLOR = vg.nvgRGB(70,130,200) #价格颜色
    MAIN_COLOR = vg.nvgRGB(255,0,255) #主力
    HUGE_COLOR = vg.nvgRGB(139,0,0)
    LARG_COLOR = vg.nvgRGB(255,0,0)
    MA5_COLOR = vg.nvgRGB(255,0,255)
    MID_COLOR = vg.nvgRGB(255,215,0)
    TING_COLOR = vg.nvgRGB(135,206,250)
    RED_COLOR = vg.nvgRGB(220,0,0)   #涨
    GREEN_COLOR = vg.nvgRGB(0,120,0) #跌
    BG_COLOR = vg.nvgRGB(255,255,255) #背景

    YLABELWIDTH = 40   #y轴坐标轴空间
    XLABELHEIGHT = 30  #x轴坐标轴空间

    ORDER_BGCOLOR = vg.nvgRGB(220,220,220)
    ORDER_HEADCOLOR = vg.nvgRGB(64,96,196)
    ORDER_SELCOLOR = vg.nvgRGB(196,96,96)
    ORDER_TEXTBGCOLOR = vg.nvgRGBA(64,64,64,255)
    ORDER_TEXTCOLOR = vg.nvgRGB(255,255,255)  

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
    MID_COLOR = vg.nvgRGB(255,215,0)
    TING_COLOR = vg.nvgRGB(135,206,250)
    RED_COLOR = vg.nvgRGB(250,0,0)   #涨
    GREEN_COLOR = vg.nvgRGB(0,200,0) #跌
    BG_COLOR = vg.nvgRGB(0,0,0) #背景

    YLABELWIDTH = 40   #y轴坐标轴空间
    XLABELHEIGHT = 30  #x轴坐标轴空间

    ORDER_BGCOLOR = vg.nvgRGB(0,0,0)
    ORDER_HEADCOLOR = vg.nvgRGB(0,0,0)
    ORDER_SELCOLOR = vg.nvgRGB(32,96,168)
    ORDER_TEXTBGCOLOR = vg.nvgRGBA(0,0,0,255)
    ORDER_TEXTCOLOR = vg.nvgRGB(255,255,255)  

    ORDER_WIDTH = 150       #排序栏宽度
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
    RTK = 0  #更新RT
    BOLLWAY = 1
    def __init__(self):
        self._kplot = frame.Plot()
        self._vplot = frame.Plot()
        self._kplot.setThemos(Themos)
        self._vplot.setThemos(Themos)
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
        self._upmode = StockPlot.RTK
    def clear(self):
        self._code = None
        self._k = None
        self._d = None
        self._mm = None 
        self._kplot.setTitle('')
        self._kplot.clear()
        self._vplot.clear()
    def forcus(self,b):
        self._forcus = b
    def getKlineData(self,code,period,knum,off):
        KDN = len(StockPlot.KD)
        if period==5 or period=='d':
            bi = KDN-off-knum-60 #确保60日均线计算是正确的
            if bi<0:
                bi=0
            after = stock.dateString(StockPlot.KD[bi][0])
            c,k,d = stock.loadKline(code,period,after=after)
        else:
            bi = KDN-math.ceil((off+knum+320)/(240/period))
            if bi<0:
                bi=0
            after = stock.dateString(StockPlot.KD[bi][0])
            c,k,d = stock.loadKline(code,5,after=after)
            if period!=5:
                k,d = stock.mergeK(k,d,int(period/5))
        
        if off==0 and stock.isTransDay():
            _,k,d = xueqiu.appendK(code,period,k,d)
        if off==0:
            return c,k,d
        else:
            return c,k[:-off],d[:-off]
    def updateK(self,code,label,period,knum,kei): #更新K线图
        self._code = code
        self._upmode = StockPlot.RTK
        _,k,d = self.getKlineData(code,period,knum,kei)
        if period!='d':
            ma5 = stock.ma(k[:,4],80)
            ma20 = stock.ma(k[:,4],320)
        else:
            ma5 = stock.ma(k[:,4],5)
            ma20 = stock.ma(k[:,4],20)
        bi = -knum
        ei = k.shape[0]
        
        x = np.arange(len(k[bi:ei]))
        xticks = []
        D = d[bi:ei]
        for i in range(len(D)-1):
            if type(period)==int:
                if (D[i][0].day!=D[i+1][0].day):
                    t = D[i][0]
                    xticks.append((i,'%2d-%2d'%(t.month,t.day)))        
            else:
                if D[i][0].weekday()==0:
                    t = D[i][0]
                    xticks.append((i,'%2d-%2d'%(t.month,t.day)))                   
        self._kplot.setx(x)
        self._kplot.setTicks(xticks)
        K = k[bi:ei,1:]
        self._kplot.plot(K,color=Themos.PRICE_COLOR,style=frame.Plot.K)
        self._kplot.plot(ma5[bi:ei],label='ma5',color=Themos.MAIN_COLOR,linewidth=2,linestyle=(4,2,0))
        self._kplot.plot(ma20[bi:ei],label='ma20',color=Themos.LARG_COLOR,linewidth=4,linestyle=(4,2,0))
        self._vplot.setx(x)
        self._vplot.setTicks(xticks)
        self._vplot.setTicksAngle(25)
        color = [Themos.RED_COLOR if K[i,0]<K[i,3] else Themos.GREEN_COLOR for i in range(K.shape[0])]
        self._vplot.plot(k[bi:ei,0],color=color,style=frame.Plot.BAR)
        self._kplot.setGrid(True,True)
        self._vplot.setGrid(True,True)
        self._kplot.setTitle(label)
        self._kplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        self._vplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        return kei
    def viewMode(self,km=None,vm=None):
        if km is not None:
            self._kmode = km
        if vm is not None:
            self._vmode = vm
    def update(self,code,label,ok,od,ma5b=None,ma60b=None,isem933=False): #更新线图
        self._upmode = StockPlot.RTK
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
        self._kplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        self._vplot.setOuterSpace(Themos.YLABELWIDTH,0,0,0)
        if ma5b is not None and len(d)>0:
            ma5 = np.zeros((len(k),))
            ma5[0] = ma5b[0]
            k15b = ma5b[1]
            N = 240*5
            M = 15
            for i in range(1,len(k)):
                ma5[i] = ma5[i-1]+(k[i,0]-k15b[int(i/M)])/(N) #这是一个近似迭代
            self._kplot.plot(ma5,color=Themos.MA5_COLOR,linewidth=2,linestyle=(6,3,0))
    def updateBollWay(self,code,label,k,d,period):
        self._code = code
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

    def render(self,canvas,x,y,w,h,xaxis=False,scale=1):
        if self._upmode==StockPlot.RTK:
            self.renderRTK(canvas,x,y,w,h,xaxis=xaxis,scale=scale)
        elif self._upmode==StockPlot.BOLLWAY:
            self.renderBollWay(canvas,x,y,w,h,xaxis=xaxis,scale=scale)
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
    def renderRTK(self,canvas,x,y,w,h,xaxis=False,scale=1):
        if self._forcus:
            canvas.beginPath()
            canvas.fillColor(Themos.SELBGCOLOR)
            canvas.rect(x+Themos.YLABELWIDTH,y,w-Themos.YLABELWIDTH,h)
            canvas.fill()
        self._kplot.setAxisVisiable(False,True)
        self._vplot.setAxisVisiable(xaxis,True)
        if self._forcus:
            scale = 1
        self._kplot.setLineWidthScale(scale)
        self._vplot.setLineWidthScale(scale)
        self._kplot.render(canvas,x,y,w,h*2/3)
        self._vplot.render(canvas,x,y+h*2/3,w,h/3)
        if self._k is not None and self._k.shape[0]>0: #显示每天的高点和低点
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
        
class StockOrder:
    """
    管理一个股票列表,(0 code,1 label,2 oder data,3 color,...)
    """
    def __init__(self):
        self._ls = []
        self._pagei = 0
        self._pagen = 1
    def update(self,ls,pagei,pagen):
        self._ls = ls
        self._pagei = pagei
        self._pagen = pagen
    def render(self,canvas,x,y,w,h):
        yy = y
        canvas.textAlign(vg.NVG_ALIGN_LEFT|vg.NVG_ALIGN_MIDDLE)
        canvas.fontFace("zh")
        canvas.fontSize(Themos.ORDER_FONTSIZE)
        for i in range(len(self._ls)):
            it = self._ls[i]
            if yy-y<h:
                canvas.beginPath()
                canvas.fillColor(Themos.ORDER_BGCOLOR)
                canvas.rect(x,yy,Themos.ORDER_WIDTH,Themos.ORDER_ITEM_HEIGHT)
                canvas.fill() #绘制背景
                canvas.beginPath()
                canvas.fillColor(Themos.ORDER_TEXTBGCOLOR)
                canvas.rect(x+76,yy,Themos.ORDER_WIDTH-76,Themos.ORDER_ITEM_HEIGHT)
                canvas.fill() #绘制文字背景
                canvas.beginPath()
                canvas.fillColor(Themos.ORDER_SELCOLOR if i>=self._pagei*self._pagen and i<(self._pagei+1)*self._pagen else Themos.ORDER_HEADCOLOR)
                canvas.rect(x,yy,25,Themos.ORDER_ITEM_HEIGHT)
                canvas.fill() #绘制序号背景
                canvas.fillColor(Themos.ORDER_TEXTCOLOR)
                canvas.text(x+5,yy+Themos.ORDER_ITEM_HEIGHT/2,str(i+1))
                canvas.fillColor(Themos.ORDER_TEXTCOLOR)
                canvas.text(x+78,yy+Themos.ORDER_ITEM_HEIGHT/2,it[1])
                #绘制涨跌幅
                it[2]
                canvas.fillColor(Themos.RED_COLOR if it[2]>0 else Themos.GREEN_COLOR)
                canvas.text(x+30,yy+Themos.ORDER_ITEM_HEIGHT/2,"%.02f%%"%it[2])
            else:
                break
            yy+=Themos.ORDER_ITEM_HEIGHT
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
    盯盘应用 
    F1 ETF F2 概念 F3 行业 F4 大盘 F5 持有 F6 关注
    Ctrl+1,4,6,8股同屏  PageDown PageUp翻页 Home首页 End尾页 ,INSERT 反转排序 1,2,3,4,5,6直接选择个股
    ENTER 切换选择的个股到K图, Ctrl+ENTER 全部切换到K图
    F5 涨幅排序 F6 净量排序 F7 流入排序 F8 量比排序 F1帮助
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
    def __init__(self,title,w,h):
        super(HotPlotApp,self).__init__(title,w,h)
        self._numsub = (3,2) #同屏数量 1 (1,1),4 (2,2),6 (3,2)
        self._oldnumsub = self._numsub
        self._oldpagen = 0
        self._SO = StockOrder()
        self._SPV = [StockPlot() for i in range(10)]
        self.setInterval(0)
        self._prefix = ('2',) #选择分类
        self._flowin = False #净流入
        self._hasboll = False #有通道
        self._reverse = False #排序
        self._em933 = False 
        self._pagen = 0 #页面
        self._topn = 64
        self._order = 0
        self._current = None
        self._help = False
        self._helpimg = None
        self._filter = ''
        self._knum = 200 #屏幕上放置k线的数量
        self._kei = 0
        self._period = 15
        self._volmode = StockPlot.FLOW
        self._kmode = HotPlotApp.RT
        self._K = None
        self._D = None   
        self._Data = None   
        self.setClearColor(Themos.BGCOLOR)
        self._ltt = datetime.today()
        self._lut = self._ltt
        threading.Thread(target=self.update_data_loop).start()
        self._needUpdate = False
    def update_data_loop(self):
        while self._running:
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
                self._needUpdate = True
                self._Data = (k,d,k15,d15,[],e)
            sdl2.SDL_Delay(100)
    def getCurrentRT(self):
        return self._Data
    def onLoop(self,t,dt):
        tt = datetime.today()
        if tt.second!=self._ltt.second:
            self._ltt = tt
            self.setWindowTitle('%d月%d日 %02d:%02d:%02d'%(tt.month,tt.day,tt.hour,tt.minute,tt.second)) 
        if self._needUpdate: #每分钟更新一次
            self._needUpdate = False
            self.updatedata()
            self.update()
    def render(self,dt,w,h):
        try:
            self._canvas.beginFrame(w,h,1)
            self._SO.render(self._canvas,0,0,Themos.ORDER_WIDTH,h)
            col = self._numsub[0]
            raw = self._numsub[1]
            dw = (w-Themos.ORDER_WIDTH-10)/col
            dh = (h-Themos.XLABELHEIGHT)/raw
            scale = scale=w/(720*self._numsub[0])
            if scale<1:
                scale=1
            if scale>2:
                scale=2
            for xi in range(col):
                for yi in range(raw):
                    self._SPV[yi*col+xi].render(self._canvas,xi*dw+Themos.ORDER_WIDTH,yi*dh,dw,dh,xaxis=yi==raw-1,scale=scale)

            #graph.update(dt)
            #graph.render(self._canvas,5,5)
            if self._help:
                if self._helpimg is None:
                    _path = '/'.join(str.split(__file__,'\\')[:-1])
                    self._helpimg = self._canvas.createImage('%s/images/hothelp.png'%_path,0)
                with self._canvas as canvas:
                    imgw,imgh = canvas.imageSize(self._helpimg)
                    paint = canvas.imagePattern(0,0,imgw,imgh,0,self._helpimg,1)
                    canvas.beginPath()
                    canvas.scale(w/imgw,h/imgh)
                    canvas.rect(0,0,imgw,imgh)
                    canvas.fillPaint(paint)
                    canvas.fill()
            elif self._helpimg is not None:
                self._canvas.deleteImage(self._helpimg)
                self._helpimg = None
            self._canvas.endFrame()
        except Exception as e:
            mylog.printe(e)
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
    def updatedata_imp(self):
        if self._order==0:
            tops = self.riseTop(self._topn)
        elif self._order==1: #大盘
            tops = self.mapCode2DataSource(['SH000001','SZ399001','SZ399006','SH000688'])
        elif self._order==2: #持有
            tops = self.mapCode2DataSource(stock.getHoldStocks())
        elif self._order==3: #关注
            tops = self.mapCode2DataSource(self.getFav())
        elif self._order==4: #昨日
            tops = self.mapCode2DataSource(self.getYesterdayTop(1))
        elif self._order==5: #前天
            tops = self.mapCode2DataSource(self.getYesterdayTop(2))  
        elif self._order==6: #最近活跃               
            tops = self.mapCode2DataSource(self.activeTop())  
        R = []
        TOPS = []
        if len(self._filter)==0:
            for it in tops:
                R.append((it[0][1],it[0][2],it[1],self.getGrowColor(it[1])))
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
                    R.append((it[0][1],it[0][2],it[1],self.getGrowColor(it[1])))
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
        self._SO.update(R,self._pagen,PageNum)
        if self._period!=15 and self._kmode==HotPlotApp.BULLWAY:
            K,D = xueqiu.get_period_k(240 if self._period=='d' else self._period)
        for i in range(NS[0]*NS[1]):
            j = self._pagen*PageNum+i
            self._SPV[i].clear()
            if j<len(TOPS):
                it = TOPS[j]
                k = it[2] 
                for s in range(1,len(k)):#处理价格为零的情况
                    if k[s,0]==0:
                        k[s,0] = k[s-1,0]
                if self._current is not None and i==self._current:
                    title = "%s %s"%(it[0][2],"%d分钟"%self._period if type(self._period)==int else "日线")
                    self._kei = self._SPV[i].updateK(it[0][1],title,self._period,self._knum,self._kei)
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
                            self._SPV[i].update(it[0][1],title,K,D,isem933=True,ma60b=rtk)
                        else:
                            self._SPV[i].update(it[0][1],title,K,D,ma5b=self.getma5b(it[4],it[5]))
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
    def em933(self,K,D): #补全，使得长度固定为30分钟
        d = []
        for i in range(len(D)):
            d.append(D[i])
        while d[-1].hour==9:
            d.append(d[-1]+timedelta(seconds=5))
        k = np.empty((len(d),K.shape[1]))
        k[:K.shape[0],:] = K[:,:]
        if len(d)>len(D):
            k[K.shape[0]:,:] = NaN #NaN Plot将不显示
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
        if sym==sdl2.SDLK_F1: #ETF
            if mod&sdl2.KMOD_CTRL: #ctrl+F1帮助
                self._help = True
            else:
                if self._order==1:
                    self._numsub = self._oldnumsub
                self._order = 0
                self._current = None
                self._prefix=('2',)
                self.setWindowTitle('ETF')
        elif sym==sdl2.SDLK_F2: #概念
            if self._order==1:
                self._numsub = self._oldnumsub
            self._order = 0
            self._current = None
            self._prefix=('91',)
            self.setWindowTitle('概念')
        elif sym==sdl2.SDLK_F3: #行业
            if self._order==1:
                self._numsub = self._oldnumsub
            self._order = 0
            self._current = None
            self._prefix=('90',)
            self.setWindowTitle('行业')
        elif sym==sdl2.SDLK_F4: #大盘
            self._order = 1
            self._current = None
            self._oldnumsub = self._numsub
            self._numsub = (2,2)
            self._prefix=('90',)
            self.setWindowTitle('大盘')
        elif sym==sdl2.SDLK_F5: #持有
            self._order = 2
            self._current = None
            self.setWindowTitle('持有')
        elif sym==sdl2.SDLK_F6: #关注
            self._order = 3
            self._current = None
            self.setWindowTitle('关注')
        elif sym==sdl2.SDLK_F7: #昨日排行
            self._order = 4
            self._current = None
            self.setWindowTitle('昨日排行')
        elif sym==sdl2.SDLK_F8: #前天排行
            self._order = 5
            self._current = None
            self.setWindowTitle('前天排行')
        elif sym==sdl2.SDLK_F9: #个股
            if self._order==1:
                self._numsub = self._oldnumsub            
            self._order = 0
            self._current = None
            self._prefix=('1','0')
            self.setWindowTitle('个股')            
        elif sym==sdl2.SDLK_F10: #活跃的
            if self._order==1:
                self._numsub = self._oldnumsub              
            self._order = 6
            self._current = None
            self.setWindowTitle('最近活跃')
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
            self._current = None
            self._kei = 0
            self._pagen-=1
        elif sym==sdl2.SDLK_PAGEDOWN:
            self._current = None
            self._kei = 0
            self._pagen+=1
        elif sym==sdl2.SDLK_HOME:
            self._current = None
            self._kei = 0
            self._pagen = 0
        elif sym==sdl2.SDLK_END:
            self._current = None
            self._kei = 0
            self._pagen = 1e10
        elif sym==sdl2.SDLK_INSERT:
            self._current = None
            self._kei = 0
            self._reverse = not self._reverse
        elif sym==sdl2.SDLK_LEFT:
            self._kei += int(self._knum/4)
        elif sym==sdl2.SDLK_RIGHT:
            self._kei -= int(self._knum/4)
            if self._kei<0:
                self._kei = 0
        elif sym==sdl2.SDLK_UP:
            self._knum += 10
            if self._knum>400:
                self._knum=400
        elif sym==sdl2.SDLK_DOWN:
            self._knum -= 10
            if self._knum<60:
                self._knum=60
        elif sym==sdl2.SDLK_KP_9:
            p = {5:0,15:1,30:2,60:3,'d':4}
            pp = [5,15,30,60,'d']
            i = p[self._period]+1
            self._period = pp[i] if i<=4 else pp[0]
        elif sym==sdl2.SDLK_KP_DIVIDE:
            self._em933 = not self._em933
        elif sym==sdl2.SDLK_KP_8:
            if self._volmode==StockPlot.FLOW:
                self._volmode = StockPlot.VOL
            elif self._volmode==StockPlot.VOL:
                self._volmode = StockPlot.LMR
            else:
                self._volmode = StockPlot.FLOW
        elif sym==sdl2.SDLK_KP_7:
            if self._kmode==HotPlotApp.RT:#切换实时图和15分钟通道图和早盘实时图
                self._kmode=HotPlotApp.BULLWAY
            else:
                self._kmode=HotPlotApp.RT
        elif sym==sdl2.SDLK_KP_0:
            pass
        elif sym==sdl2.SDLK_KP_PERIOD:
            pass
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
            if mod&sdl2.KMOD_CTRL and self._order!=2:#增加持有
                code = self._SPV[self._current]._code
                stock.holdStock(code,True)
                self._current = None
            if mod&sdl2.KMOD_CTRL and self._order==2:#删除持有
                code = self._SPV[self._current]._code
                stock.holdStock(code,False)
                self._current = None
            if mod&sdl2.KMOD_ALT and self._order!=3:#增加关注
                code = self._SPV[self._current]._code
                name = HotPlotApp.code2com[code][2]
                stock.execute("insert into notebook (date,code,name,context,note) values ('%s','%s','%s','%s','%s')"%(stock.dateString(date.today()),code,name,'HotPlotApp',''))
                self._current = None
            if mod&sdl2.KMOD_ALT and self._order==3:#删除关注
                code = self._SPV[self._current]._code
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
        self.updatedata()
        self.update()
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
                R.append((companys[i],k[i,-1,1],k[i],d,K[i],D,bolls)) #0 company,1 涨幅(排序项) 2 k 3 d 4 K15 5 D15 6 bolls
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
            R.append((companys[i],k[i,-1,1],k[i],d,K[i],D,bolls))
        return R#[:top]
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

class MyPlotApp(frame.app):
    def __init__(self,title,w,h):
        super(MyPlotApp,self).__init__(title,w,h)
        self._myplot = frame.Plot()
        self._volplot = frame.Plot()
        #x = np.arange(100)
        #y = np.sin(x*4*np.pi/200)
        #y2 = np.cos(x*4*np.pi/200)
        k,d = xueqiu.get_rt(4)
        companys = xueqiu.get_company_select()
        #y = x#np.sin(x)
        for i in range(len(companys)):
            com = companys[i]
            if com[1]=='SH516780':
                self._myplot.setTitle(com[2])
                x = np.arange(len(d))
                self._myplot.setx(x)
                self._myplot.plot(k[i,:,0])
                ma60 = stock.ma(k[i,:,0],60)
                self._myplot.plot(ma60,color=vg.nvgRGBf(1,0.4,0.2),linestyle=(4,2,0))
                self._volplot.setx(x)
                hug = np.copy(k[i,:,3]+k[i,:,4])
                hug[hug!=hug]=0
                self._volplot.plot(hug,color=vg.nvgRGBf(1,0,1),linewidth=3)#,linestyle=(4,2,0))
                ting = np.copy(k[i,:,6])
                ting[ting!=ting]=0
                self._volplot.plot(ting,color=vg.nvgRGBf(0,0,0.6))
        self._myplot.setGrid(True)
        self._volplot.setGrid(True)
        self._volplot.setOuterSpace(80,0,0,0)
        self._myplot.setOuterSpace(80,0,0,50)

        self._myk = frame.Plot()
        c,k,d = stock.loadKline('SH516780','d')
        self._myk.setTitle(c[2])
        MA20 = stock.ma(k[:,4],20)
        K = k[-200:,1:]
        self._myk.setx(np.arange(K.shape[0]))
        self._myk.plot(K,style=frame.Plot.K)
        #self._myk.plot(MA20[-200:],color=vg.nvgRGB(0,0,255),linewidth=2)
        self._myk.setGrid(True)
        self._myk.setOuterSpace(80,0,0,0)
        self._myk.setInnerSpace(10,10,0,0)
        #self._myk.setTicksAngle(-45,-45)
    def render(self,dt,w,h):
        self._canvas.beginFrame(w, h,1)
        #self._myplot.render(self._canvas,15,15,w-30,h/2)
        #self._volplot.render(self._canvas,15,h/2-15,w-30,h/2-30)
        self._myk.render(self._canvas,15,15,w-30,h/2)
        graph.update(dt)
        graph.render(self._canvas,5,5)
        self._canvas.endFrame()

    def keyDown(self,event):
        if event.keysym.sym==ord('q'):#sdl2.SDLK_a:
            self.quit()

"""
glwin = MyPlotApp('图表',640,480)
graph = frame.fpsGraph()
glwin.setInterval(10)
glwin.run()
"""
glwin = HotPlotApp('图表',1600,800)
graph = frame.fpsGraph()
glwin.run()
