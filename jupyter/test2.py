from app.nanovg import frame,vg
from app import monitor,xueqiu,stock
from datetime import date,datetime,timedelta
import numpy as np
import math
import sdl2
from OpenGL import GL
import ctypes

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
class StockPlot:
    """
    包括两个区域，分时和成交量流入流出区
    """
    YLABELWIDTH = 40
    XLABELHEIGHT = 30
    PRICE_COLOR = vg.nvgRGB(70,130,200)
    MAIN_COLOR = vg.nvgRGB(255,0,255)
    HUGE_COLOR = vg.nvgRGB(139,0,0)
    LARG_COLOR = vg.nvgRGB(255,0,0)
    MID_COLOR = vg.nvgRGB(255,215,0)
    TING_COLOR = vg.nvgRGB(135,206,250)
    def __init__(self):
        self._kplot = frame.Plot()
        self._vplot = frame.Plot()
    def update(self,code,label,k,d):
        x = np.arange(len(d))
        self._kplot.setx(x)
        self._kplot.plot(k[:,0],color=StockPlot.PRICE_COLOR)
        self._vplot.setx(x)
        self._vplot.plot(k[:,3]+k[:,4],color=StockPlot.MAIN_COLOR)
        self._vplot.plot(k[:,3],color=StockPlot.HUGE_COLOR)
        self._vplot.plot(k[:,4],color=StockPlot.LARG_COLOR)
        self._vplot.plot(k[:,5],color=StockPlot.MID_COLOR)
        self._vplot.plot(k[:,6],color=StockPlot.TING_COLOR)
        self._kplot.setGrid(True,True)
        self._vplot.setGrid(True,False)
        self._kplot.setTitle(label)
        self._kplot.setOuterSpace(StockPlot.YLABELWIDTH,0,0,0)
        self._vplot.setOuterSpace(StockPlot.YLABELWIDTH,0,0,0)
    def render(self,canvas,x,y,w,h,xaxis=False):
        self._kplot.setAxisVisiable(False,True)
        self._vplot.setAxisVisiable(xaxis,True)
        self._kplot.render(canvas,x,y,w,h*2/3)
        self._vplot.render(canvas,x,y+h*2/3,w,h/3)
class StockOrder:
    """
    管理一个股票列表,(0 code,1 label,2 oder data,3 color,...)
    """
    WIDTH = 120
    HEIGHT = 32
    TEXTCOLOR = vg.nvgRGB(255,255,255)
    FONTSIZE = 14
    def __init__(self):
        self._ls = []
    def update(self,ls):
        self._ls = ls
    def render(self,canvas,x,y,w,h):
        yy = y
        canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_MIDDLE)
        canvas.fontFace("zh")
        canvas.fontSize(StockOrder.FONTSIZE)
        for i in range(len(self._ls)):
            it = self._ls[i]
            if yy-y<h:
                canvas.beginPath()
                canvas.fillColor(vg.nvgRGB(*it[3]))
                canvas.rect(x,yy,StockOrder.WIDTH,StockOrder.HEIGHT)
                canvas.fill()
                canvas.fillColor(StockOrder.TEXTCOLOR)
                canvas.text(x+StockOrder.WIDTH/2,yy+StockOrder.HEIGHT/2,it[1])
            else:
                break
            yy+=StockOrder.HEIGHT
class DateLabel:
    """
    显示一个日期包括时间
    """
    TEXTCOLOR = vg.nvgRGB(0,0,0)
    SIZE = 14
    def __init__(self):
        pass
    def render(self,canvas,x,y,w,h):
        canvas.textAlign(vg.NVG_ALIGN_CENTER|vg.NVG_ALIGN_MIDDLE)
        canvas.beginPath()
        t = datetime.today()
        canvas.fillColor(DateLabel.TEXTCOLOR)
        canvas.fontFace("zh")
        canvas.fontSize(DateLabel.SIZE)
        canvas.text(x+w/2,y+h/2,stock.timeString2(t))
        
class HotPlotApp(frame.app):
    """
    盯盘应用 
    Ctrl+E ETF Ctrl+G 概念 Ctrl+H 行业 Ctrl+C 持有 Ctrl+Z 关注 Ctrl+D 大盘
    Ctrl+1，4，6 股同屏  PageDown PageUp翻页 Home首页 End尾页 , 1,2,3,4,5,6直接选择个股
    ENTER 切换选择的个股到K图, Ctrl+ENTER 全部切换到K图
    F5 涨幅排序 F6 净量排序 F7 流入排序 F8 量比排序 F1帮助
    """
    companys = xueqiu.get_company_select()
    code2i = xueqiu.get_company_code2i()
    code2com = xueqiu.get_company_code2com()    
    def __init__(self,title,w,h):
        super(HotPlotApp,self).__init__(title,w,h)
        self._numsub = (3,2) #同屏数量 1 (1,1),4 (2,2),6 (3,2)
        self._SO = StockOrder()
        self._SPV = [StockPlot() for i in range(6)]
        self.setInterval(0)
        self._prefix = '2' #选择分类
        self._flowin = False #净流入
        self._hasboll = False #有通道
        self._reverse = False #排序
        self._topn = 64
        self.updatedata()
    def onLoop(self,t,dt):
        pass
    def render(self,dt,w,h):
        self._canvas.beginFrame(w,h,1)
        self._SO.render(self._canvas,0,0,StockOrder.WIDTH,h)
        col = self._numsub[0]
        raw = self._numsub[1]
        dw = (w-StockOrder.WIDTH-10)/col
        dh = (h-StockPlot.XLABELHEIGHT)/raw
        for xi in range(col):
            for yi in range(raw):
                self._SPV[yi*col+xi].render(self._canvas,xi*dw+StockOrder.WIDTH,yi*dh,dw,dh,xaxis=yi==raw-1)

        #graph.update(dt)
        #graph.render(self._canvas,5,5)
        self._canvas.endFrame()
    def getGrowColor(self,r): #根据涨幅返回颜色tuple
        if r>0:
            a = r/10
            if a>1:
                a = 1
            return (int(255*a),0,0)
        else:
            a = -r/10
            if a>1:
                a = 1
            return (0,int(255*a),0)

    def updatedata(self):
        tops = self.riseTop(self._topn)
        R = []
        for it in tops:
            R.append((it[0][1],it[0][2],it[1],self.getGrowColor(it[1])))
        self._SO.update(R)
        for i in range(self._numsub[0]*self._numsub[1]):
            if i<len(tops):
                it = tops[i]
                self._SPV[i].update(it[0][1],it[0][2],it[2],it[3])
    def getCurrentRT(self):
        """
        返回当前数据
        """
        t = datetime.today()
        k,d = monitor.get_rt(4) #取得最近3天的1分钟数据(0 price,1 当日涨幅,2 volume,3 larg,4 big,5 mid,6 ting)
        bi = -255*3
        k = k[:,bi:,:]
        d = d[bi:]
        k15,d15 = xueqiu.get_period_k(15)
        for i in range(k15.shape[0]): #处理价格为0的情况
            if k15[i,0]==0:
                for j in range(k15.shape[1]):
                    if k15[i,j]!=0:
                        k15[i,:j] = k15[i,j]
                        break
                continue

        bolls = monitor.bolltrench()
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
        companys = HotPlotApp.companys
        R = []
        for i in range(len(companys)):
            if i<k.shape[0] and self.isSelected(companys[i],bolls,k[i]):
                R.append((companys[i],k[i,-1,1],k[i],d,K[i],D,bolls)) #0 company,1 涨幅(排序项) 2 k 3 d 4 K15 5 D15 6 bolls
        TOPS = sorted(R,key=lambda it:it[1],reverse=not self._reverse)
        #将三点指数追加在末尾
        return TOPS[:top]        
        

class MyPlotApp(frame.app):
    def __init__(self,title,w,h):
        super(MyPlotApp,self).__init__(title,w,h)
        self._myplot = frame.Plot()
        self._volplot = frame.Plot()
        #x = np.arange(100)
        #y = np.sin(x*4*np.pi/200)
        #y2 = np.cos(x*4*np.pi/200)
        k,d = monitor.get_rt(4)
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
glwin = HotPlotApp('图表',1280,800)
graph = frame.fpsGraph()
glwin.run()
